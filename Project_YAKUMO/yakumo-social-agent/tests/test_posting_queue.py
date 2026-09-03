import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.state import PostState
from app.database.db import Database
from app.pipeline.queue import PostingQueue
from app.x.poster import XPoster


def _seed_approved(db: Database, entry_id: str) -> None:
    db.create_new(entry_id, f"原文 {entry_id}", source_url=f"https://x.com/s/{entry_id}")
    db.transition(entry_id, PostState.ANALYZED)
    db.transition(entry_id, PostState.DRAFTED, draft_text=f"YAKUMOの投稿案 {entry_id}")
    db.transition(entry_id, PostState.WAITING_APPROVAL, discord_message_id="m1")
    db.transition(entry_id, PostState.APPROVED, approval_status="approved")


class _FakePoster:
    """Phase 5（実X投稿）がまだ未実装のため、キューのペース制御ロジック単体を
    検証するための、実際に投稿したことにするテスト用ダミー。dry_run=False固定。
    """

    def __init__(self):
        self.dry_run = False
        self.calls = 0

    def post(self, candidate) -> str:
        self.calls += 1
        return f"fake-x-post-{self.calls}"


def test_posts_first_approved_item_when_no_prior_post():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "t.db")
        db = Database(db_path)
        _seed_approved(db, "e1")

        queue = PostingQueue(db=db, poster=_FakePoster(), min_interval_minutes=30)
        posted = queue.try_post_next()

        assert posted == "e1"
        row = db.get("e1")
        assert row["state"] == PostState.POSTED.value
        assert row["x_post_id"] == "fake-x-post-1"


def test_second_item_waits_for_pace_interval():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "t.db")
        db = Database(db_path)
        _seed_approved(db, "e1")
        _seed_approved(db, "e2")

        queue = PostingQueue(db=db, poster=_FakePoster(), min_interval_minutes=30)

        first = queue.try_post_next()
        assert first == "e1"

        # 直後にもう一度呼んでも、まだ間隔が空いていないので投稿されない
        second = queue.try_post_next()
        assert second is None

        row_e2 = db.get("e2")
        assert row_e2["state"] == PostState.APPROVED.value  # まだ承認済みのまま


def test_second_item_posts_after_interval_elapses():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "t.db")
        db = Database(db_path)
        _seed_approved(db, "e1")
        _seed_approved(db, "e2")

        queue = PostingQueue(db=db, poster=_FakePoster(), min_interval_minutes=30)
        queue.try_post_next()  # e1を投稿

        # 30分以上前に投稿されたことにして、間隔が空いた状態を再現する
        past = (datetime.now(timezone.utc) - timedelta(minutes=31)).isoformat()
        with db._connect() as conn:  # noqa: SLF001
            conn.execute(
                "UPDATE posts SET x_posted_at = ? WHERE source_entry_id = ?", (past, "e1")
            )

        second = queue.try_post_next()
        assert second == "e2"


def test_dry_run_does_not_advance_state(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "t.db")
        db = Database(db_path)
        _seed_approved(db, "e1")

        poster = XPoster()  # 実物。dry_run=Trueなので例外を投げない
        queue = PostingQueue(db=db, poster=poster, min_interval_minutes=30)

        posted = queue.try_post_next()

        assert posted is None  # DRY_RUN中は「投稿した」扱いにしない
        row = db.get("e1")
        assert row["state"] == PostState.APPROVED.value  # 状態はAPPROVEDのまま
