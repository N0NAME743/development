"""指示書16章のシナリオのうち、Discord/X実接続なしで検証できるものをカバーする。

- Discord承認 / 却下 / 修正依頼 → 状態遷移として検証
- 二重クリック → 2回目のAPPROVEDが弾かれることを検証
- n8n再実行 / サーバー再起動 → 同一プロセスを2回動かしても結果が変わらないことで代替検証
  （test_dedup.py参照）
- X APIタイムアウト・失敗 → DRY_RUN時にXPosterが実際には呼び出されない安全側の動作を検証
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.common.state import InvalidTransition, PostState
from app.database.db import Database
from app.x.poster import XPoster


def _seed_waiting_approval(db: Database, entry_id: str = "e1") -> None:
    db.create_new(entry_id, "テスト用の原文")
    db.transition(entry_id, PostState.ANALYZED)
    db.transition(entry_id, PostState.DRAFTED, draft_text="テスト投稿案")
    db.transition(entry_id, PostState.WAITING_APPROVAL, discord_message_id="msg-1")


def test_discord_approval_flow():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(os.path.join(tmp, "t.db"))
        _seed_waiting_approval(db)

        db.transition("e1", PostState.APPROVED, approval_status="approved")
        db.transition("e1", PostState.POSTED, x_post_id="x-123")

        row = db.get("e1")
        assert row["state"] == PostState.POSTED.value
        assert row["x_post_id"] == "x-123"


def test_discord_rejection_flow():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(os.path.join(tmp, "t.db"))
        _seed_waiting_approval(db)

        db.transition("e1", PostState.REJECTED_BY_USER, approval_status="rejected")

        row = db.get("e1")
        assert row["state"] == PostState.REJECTED_BY_USER.value


def test_revision_request_loops_back_for_re_review():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(os.path.join(tmp, "t.db"))
        _seed_waiting_approval(db)

        db.transition(
            "e1",
            PostState.REVISION_REQUESTED,
            revision_instruction="もう少し短く",
        )
        db.transition("e1", PostState.DRAFTED, draft_text="短くした投稿案")
        db.transition("e1", PostState.WAITING_APPROVAL, discord_message_id="msg-2")

        row = db.get("e1")
        assert row["state"] == PostState.WAITING_APPROVAL.value
        assert row["draft_text"] == "短くした投稿案"


def test_double_click_approval_is_rejected():
    """二重クリック: 1回目のAPPROVED後、2回目のAPPROVED操作は不正な遷移として弾かれる。"""

    with tempfile.TemporaryDirectory() as tmp:
        db = Database(os.path.join(tmp, "t.db"))
        _seed_waiting_approval(db)

        db.transition("e1", PostState.APPROVED, approval_status="approved")

        with pytest.raises(InvalidTransition):
            db.transition("e1", PostState.APPROVED, approval_status="approved")


def test_dry_run_never_calls_real_x_api(monkeypatch, capsys):
    from app.common.models import PostCandidate

    monkeypatch.setenv("DRY_RUN", "true")
    poster = XPoster()

    result = poster.post(PostCandidate(source_entry_id="e1", content_hash="h", text="投稿文"))

    assert result == "dry-run-no-post"
    assert "DRY_RUN" in capsys.readouterr().out
