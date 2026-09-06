#!/usr/bin/env python3
"""投稿ペース制御を含む投稿キューの処理エントリーポイント。

本番では、これをsystemd等で数分おきに定期実行する想定
（run_mock.py / discord_daemon.pyとは別プロセスとして動かす）。

DISCORD_BOT_TOKENが未設定の間（Phase 4着手前）は、WAITING_APPROVALのものを
「承認された」とみなして自動的にAPPROVEDへ進める（本来は人間がDiscordで
✅を押す部分の、Phase 2用の仮の代役）。DISCORD_BOT_TOKENが設定されたら、
discord_daemon.pyが実際の承認/却下を行うため、この自動承認は行わない。

DRY_RUN=true（既定）の間は、実際にはXへ投稿せず、
「投稿されるとしたら何が出るか」を表示するだけでDBの状態も変えない。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.common.factory import build_notifier
from app.common.state import PostState
from app.database.db import Database
from app.pipeline.queue import PostingQueue
from app.x.poster import XPoster

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "yakumo.db")

MIN_POST_INTERVAL_MINUTES = int(os.getenv("MIN_POST_INTERVAL_MINUTES", "30"))


def _tweet_url(tweet_id: str) -> str:
    # ユーザー名不要の汎用パーマリンク（X側で実際のURLへリダイレクトされる）。
    return f"https://x.com/i/status/{tweet_id}"


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

    if os.getenv("DISCORD_BOT_TOKEN"):
        # Phase 4稼働中: discord_daemon.pyが実際の承認/却下を行うため、
        # ここでの自動承認はスキップする。
        approved_count = 0
    else:
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

    if posted is not None:
        row = db.get(posted)

        if row and row["x_post_id"]:
            notifier = build_notifier()
            notifier.notify_posted(
                f"✅ Xへ投稿しました: {_tweet_url(row['x_post_id'])}\n"
                f"投稿時刻: {row['x_posted_at']}"
            )

    if posted is None and not approved_count and db.get_next_approved() is None:
        print("承認待ち・投稿待ちの項目はありません。")


if __name__ == "__main__":
    main()
