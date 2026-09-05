"""複数のエントリーポイント（poll_inbox.py, poll_github_trending.py等）で共通の、
.env設定に基づくAIProvider / Notifierの組み立てロジック。
"""

import os

from app.ai.base import AIProvider
from app.notify.base import Notifier
from app.notify.console_notifier import ConsoleNotifier


def build_ai_provider() -> AIProvider:
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


def build_notifier() -> Notifier:
    bot_token = os.getenv("DISCORD_BOT_TOKEN")

    if not bot_token:
        return ConsoleNotifier()

    guild_id = os.getenv("DISCORD_GUILD_ID")
    channel_id = os.getenv("DISCORD_CHANNEL_ID")

    if not guild_id or not channel_id:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN is set but DISCORD_GUILD_ID / DISCORD_CHANNEL_ID is not. "
            "USER ACTION REQUIRED: see docs/credentials.md section 2."
        )

    from app.notify.discord_bot import DiscordBotNotifier

    return DiscordBotNotifier(
        bot_token=bot_token, guild_id=guild_id, channel_id=channel_id
    )
