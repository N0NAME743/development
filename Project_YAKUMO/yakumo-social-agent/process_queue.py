#!/usr/bin/env python3
"""投稿ペース制御を含む投稿キューの処理エントリーポイント。

本番では、これをsystemd等で数分おきに定期実行する想定
（run_mock.py / 実際のDiscord Botとは別プロセスとして動かす）。

Phase 4（Discord Bot）が無い現時点では、WAITING_APPROVALのものを
「承認された」とみなして自動的にAPPROVEDへ進める（本来は人間がDiscordで
✅を押す部分の、Phase 2用の仮の代役）。

DRY_RUN=true（既定）の間は、実際にはXへ投稿せず、
「投稿されるとしたら何が出るか」を表示するだけでDBの状態も変えない。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.common.state import PostState
from app.database.db import Database
from app.pipeline.queue import PostingQueue
from app.x.poster import XPoster

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "yakumo.db")

MIN_POST_INTERVAL_MINUTES = int(os.getenv("MIN_POST_INTERVAL_MINUTES", "30"))


def _auto_approve_waiting(db: Database) -> int:
    """Phase 4未実装の間の仮代役: WAITING_APPROVALを全て承認済みにする。"""

    count = 0

    with db._connect() as conn:  # noqa: SLF001 — Phase2デモ限定の簡易実装
        rows = conn.execute(
            "SELECT source_entry_id FROM posts WHERE state = ?",
            (PostState.WAITING_APPROVAL.value,),
        ).fetchall()

    for row in rows:
        db.transition(
            row["source_entry_id"], PostState.APPROVED, approval_status="approved"
        )
        count += 1

    return count


def main() -> None:
    if not os.path.exists(DB_PATH):
        print("data/yakumo.db がありません。先に python3 run_mock.py を実行してください。")
        return

    db = Database(DB_PATH)

    approved_count = _auto_approve_waiting(db)

    if approved_count:
        print(
            f"[Phase2仮実装] WAITING_APPROVALだった{approved_count}件を自動承認しました "
            "(本来はDiscordでの人間承認)"
        )

    poster = XPoster()
    queue = PostingQueue(db=db, poster=poster, min_interval_minutes=MIN_POST_INTERVAL_MINUTES)

    print(f"DRY_RUN={poster.dry_run} / 最低投稿間隔={MIN_POST_INTERVAL_MINUTES}分")
    print()

    posted = queue.try_post_next()

    if posted is None and not approved_count and db.get_next_approved() is None:
        print("承認待ち・投稿待ちの項目はありません。")


if __name__ == "__main__":
    main()
