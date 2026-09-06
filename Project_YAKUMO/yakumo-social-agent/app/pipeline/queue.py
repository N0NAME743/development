"""投稿ペース制御。

指示書のDRY_RUN安全装置に加え、Discordで承認された投稿が複数溜まっていても、
実際のXへの投稿は最低間隔を空けて1件ずつ行うキュー機構を追加する。

承認(APPROVED)はDiscordから即座に行えるが、実際のXへの投稿はこのキューを
定期的に呼び出すジョブ（process_queue.py、systemd等で数分おきに実行）が
間隔を空けて1件ずつ処理する。

DRY_RUN=true の間は、実際には投稿せず「投稿するとしたら何が出るか」を表示するだけで、
DBの状態もAPPROVEDのまま変更しない（DRY_RUNを解除した後に本当に投稿できるようにするため）。
"""

from datetime import datetime, timezone

from app.common.models import PostCandidate
from app.common.state import PostState
from app.database.db import Database
from app.x.poster import XPoster


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PostingQueue:
    def __init__(self, db: Database, poster: XPoster, min_interval_minutes: int):
        self.db = db
        self.poster = poster
        self.min_interval_minutes = min_interval_minutes

    def _seconds_since_last_post(self) -> float | None:
        last = self.db.get_last_posted_at()

        if not last:
            return None

        last_dt = datetime.fromisoformat(last)
        now = datetime.now(timezone.utc)

        return (now - last_dt).total_seconds()

    def try_post_next(self) -> str | None:
        """ペース制御の間隔が空いていれば、承認済みの最古の1件を投稿する。

        まだ間隔が空いていない、または承認済みが無ければ何もしない。
        戻り値: 実際に投稿した場合はsource_entry_id、しなければNone。
        """

        elapsed = self._seconds_since_last_post()
        min_seconds = self.min_interval_minutes * 60

        if elapsed is not None and elapsed < min_seconds:
            remaining_min = int((min_seconds - elapsed) // 60)
            print(f"[queue] ペース制御中: 次に投稿できるまであと約{remaining_min}分")
            return None

        next_row = self.db.get_next_approved()

        if next_row is None:
            return None

        candidate = PostCandidate(
            source_entry_id=next_row["source_entry_id"],
            content_hash=next_row["content_hash"],
            text=next_row["draft_text"] or "",
            source_url=next_row["source_url"],
        )

        try:
            x_post_id = self.poster.post(candidate)
        except Exception as e:
            # 失敗したままAPPROVEDに留めると、次回実行時にget_next_approved()が
            # 同じ内容を再び拾って同じ失敗（例: X APIの重複投稿拒否）を繰り返す。
            # FAILEDへ遷移させ、同じ投稿の自動再送を止める（指示書12章）。
            self.db.transition(
                next_row["source_entry_id"],
                PostState.FAILED,
                error_message=str(e),
            )
            print(
                f"[queue] X投稿失敗、再送しないようFAILEDにしました: "
                f"source_entry_id={next_row['source_entry_id']} ({e})"
            )
            return None

        if self.poster.dry_run:
            # DRY_RUN中は「投稿されるべき状態」を確認するだけで、
            # 実際にはAPPROVEDのまま据え置く（DRY_RUN解除後に本当に投稿できるように）。
            print(
                f"[queue] [DRY_RUN] 実投稿ならここで投稿されます: "
                f"source_entry_id={next_row['source_entry_id']}"
            )
            return None

        self.db.transition(
            next_row["source_entry_id"],
            PostState.POSTED,
            x_post_id=x_post_id,
            x_posted_at=_now(),
        )
        print(f"[queue] 投稿完了: source_entry_id={next_row['source_entry_id']}")

        return next_row["source_entry_id"]
