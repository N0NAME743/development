#!/usr/bin/env python3
"""Phase 3 エントリーポイント（実データ版）。

run_mock.py と同じパイプラインを、Mockではなく実際の
「記録_Research INBOX」（Notion）と実AI（既定: Gemini）で実行する。

Discord Bot（Phase 4）・X投稿（Phase 5）はまだ未実装のため、
通知はまだConsole表示のまま（承認・投稿ペース制御を試すには process_queue.py を使う）。

必要な環境変数（.env。docs/credentials.md 参照）:
  NOTION_TOKEN, NOTION_DATA_SOURCE_ID   — 記録_Research INBOXの認証情報（既存パイプラインと共用可）
  NOTION_AI_HANTEI_VALUE                — 対象とするAI査定の値（既定: "🟢 IDEA BOXへ"）
  AI_PROVIDER                           — "gemini"（既定・無料枠あり） | "anthropic" | "openai"
  GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY — 選んだAI_PROVIDER用（AI_API_KEYでも可）

本番では、これをsystemd等で定期実行（例: 15分おき）する想定
（process_queue.py とは別プロセス）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.ai.base import AIProvider
from app.database.db import Database
from app.notify.console_notifier import ConsoleNotifier
from app.pipeline.runner import PipelineRunner
from app.source.notion_inbox_source import NotionInboxSource

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "yakumo.db")


def _build_ai_provider() -> AIProvider:
    provider_name = os.getenv("AI_PROVIDER", "gemini").lower()

    if provider_name == "gemini":
        from app.ai.gemini_provider import GeminiProvider

        return GeminiProvider()

    if provider_name == "anthropic":
        from app.ai.anthropic_provider import AnthropicProvider

        return AnthropicProvider()

    if provider_name == "openai":
        from app.ai.openai_provider import OpenAIProvider

        return OpenAIProvider()

    raise RuntimeError(
        f"Unknown AI_PROVIDER: {provider_name!r}. "
        "Use 'gemini' (default), 'anthropic', or 'openai'."
    )


def _build_source() -> NotionInboxSource:
    token = os.getenv("NOTION_TOKEN")
    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")

    if not token or not data_source_id:
        raise RuntimeError(
            "NOTION_TOKEN / NOTION_DATA_SOURCE_ID not set. "
            "USER ACTION REQUIRED: see docs/credentials.md section 4."
        )

    ai_hantei_value = os.getenv("NOTION_AI_HANTEI_VALUE", "🟢 IDEA BOXへ")

    return NotionInboxSource(
        token=token, data_source_id=data_source_id, ai_hantei_value=ai_hantei_value
    )


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    db = Database(DB_PATH)
    ai_provider_name = os.getenv("AI_PROVIDER", "gemini")

    runner = PipelineRunner(
        source=_build_source(),
        ai=_build_ai_provider(),
        notifier=ConsoleNotifier(),
        db=db,
    )

    print("YAKUMO 自動投稿システム — Phase 3 実データ実行")
    print(f"DB: {DB_PATH}")
    print(f"AI Provider: {ai_provider_name}")
    print()

    results = runner.run_once()

    publishable = [c for c in results if c.ai_judgement and c.ai_judgement.publishable]
    rejected = [c for c in results if c.ai_judgement and not c.ai_judgement.publishable]

    print()

    if not results:
        print("記録_Research INBOXに新規の未処理エントリー（対象のAI査定）はありませんでした。")
    else:
        print(f"処理件数: {len(results)}件 (投稿候補: {len(publishable)} / AI却下: {len(rejected)})")

        for c in rejected:
            print(f"  却下: {c.source_entry_id} — {c.ai_judgement.reason}")

    print()
    print("承認・投稿ペース制御まで試すには（Discord Bot未実装のためPhase2同様の仮承認）:")
    print("  python3 process_queue.py")


if __name__ == "__main__":
    main()
