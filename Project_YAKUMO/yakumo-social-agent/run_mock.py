#!/usr/bin/env python3
"""Phase 2 エントリーポイント。

python3 run_mock.py だけで、
サンプル「記録_Research INBOX」データ -> AI Mock -> YAKUMOリアクション生成Mock -> Discord出力Mock
まで一気通貫で動く（実APIキー・Docker・n8n不要）。

投稿ペース制御のキュー（app/pipeline/queue.py）を試したい場合は process_queue.py を使う。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.mock_provider import MockProvider
from app.database.db import Database
from app.notify.console_notifier import ConsoleNotifier
from app.pipeline.runner import PipelineRunner
from app.source.mock_source import MockEntrySource

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "yakumo.db")


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    db = Database(DB_PATH)
    runner = PipelineRunner(
        source=MockEntrySource(),
        ai=MockProvider(),
        notifier=ConsoleNotifier(),
        db=db,
    )

    print("YAKUMO 自動投稿システム — Phase 2 Mock実行")
    print(f"DB: {DB_PATH}")
    print()

    results = runner.run_once()

    publishable = [c for c in results if c.ai_judgement and c.ai_judgement.publishable]
    rejected = [c for c in results if c.ai_judgement and not c.ai_judgement.publishable]

    print()
    print(f"処理件数: {len(results)}件 (投稿候補: {len(publishable)} / AI却下: {len(rejected)})")

    for c in rejected:
        print(f"  却下: {c.source_entry_id} — {c.ai_judgement.reason}")

    print()
    print("もう一度実行すると、同じsource_entry_idは重複防止により処理されません:")
    print("  python3 run_mock.py")
    print()
    print("承認・投稿ペース制御まで試すには:")
    print("  python3 process_queue.py")


if __name__ == "__main__":
    main()
