#!/usr/bin/env python3
"""情報源: GitHubで話題のリポジトリ（poll_inbox.pyと同じパイプライン、情報源だけ差し替え）。

DISCORD_BOT_TOKENが設定されていれば実際のDiscordへ通知する。
未設定の間はConsole表示のまま。

必要な環境変数（.env）:
  AI_PROVIDER                           — "gemini"（既定・無料枠あり） | "anthropic" | "openai"
  GEMINI_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY — 選んだAI_PROVIDER用（AI_API_KEYでも可）
  DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_CHANNEL_ID — 設定時のみDiscordへ通知
  GITHUB_TOKEN                          — 任意。未設定でも動くが、レート制限が60回/時と低くなる
  GITHUB_TRENDING_LOOKBACK_DAYS         — 既定7（何日以内に作られたリポジトリを対象にするか）
  GITHUB_TRENDING_MIN_STARS             — 既定50（最低スター数）

本番では、これをsystemd等で定期実行（例: 1日1回程度で十分）する想定
（poll_inbox.py / process_queue.py とは別プロセス）。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.common.factory import build_ai_provider, build_notifier
from app.database.db import Database
from app.notify.console_notifier import ConsoleNotifier
from app.pipeline.runner import PipelineRunner
from app.source.github_trending_source import GitHubTrendingSource

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "yakumo.db")


def _build_source() -> GitHubTrendingSource:
    return GitHubTrendingSource(
        lookback_days=int(os.getenv("GITHUB_TRENDING_LOOKBACK_DAYS", "7")),
        min_stars=int(os.getenv("GITHUB_TRENDING_MIN_STARS", "50")),
    )


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    db = Database(DB_PATH)
    ai_provider_name = os.getenv("AI_PROVIDER", "gemini")
    notifier = build_notifier()

    runner = PipelineRunner(
        source=_build_source(),
        ai=build_ai_provider(),
        notifier=notifier,
        db=db,
    )

    print("YAKUMO 自動投稿システム — GitHub Trending")
    print(f"DB: {DB_PATH}")
    print(f"AI Provider: {ai_provider_name}")
    print(f"Notifier: {type(notifier).__name__}")
    print()

    results = runner.run_once()

    publishable = [c for c in results if c.ai_judgement and c.ai_judgement.publishable]
    rejected = [c for c in results if c.ai_judgement and not c.ai_judgement.publishable]

    print()

    if not results:
        print("条件に合う新規リポジトリ（未処理）はありませんでした。")
    else:
        print(f"処理件数: {len(results)}件 (投稿候補: {len(publishable)} / AI却下: {len(rejected)})")

        for c in rejected:
            print(f"  却下: {c.source_entry_id} — {c.ai_judgement.reason}")

    print()

    if isinstance(notifier, ConsoleNotifier):
        print("承認・投稿ペース制御まで試すには（Discord Bot未設定のためPhase2同様の仮承認）:")
    else:
        print("Discordで承認/却下してください（discord_daemon.pyの常駐が必要）。")
        print("投稿ペース制御キューを進めるには:")

    print("  python3 process_queue.py")


if __name__ == "__main__":
    main()
