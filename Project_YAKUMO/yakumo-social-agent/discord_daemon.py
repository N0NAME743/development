#!/usr/bin/env python3
"""Phase 4 デーモン: Discord Botの常駐プロセス（Interaction受信専用）。

poll_inbox.py / process_queue.py は定期実行（数分〜十数分おき）で完結するが、
このプロセスだけはDiscordのボタン操作をリアルタイムで受け取るため常駐が必要
（systemd等でx-likes-notion.serviceのような永続サービスとして動かす想定）。

役割:
  ✅ 承認 → APPROVED（process_queue.pyが投稿ペース制御キューで拾う）
  ❌ 却下 → REJECTED_BY_USER
  ✏️ 修正 → モーダルで指示を受け取り、REVISION_REQUESTED として指示を保存する
            （実際の再生成はここでは行わない。次回のpoll_inbox.py拡張で
            REVISION_REQUESTEDを拾って再生成する処理は未実装 — 今後の課題）

必要な環境変数（.env。docs/credentials.md 参照）:
  DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_CHANNEL_ID
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

try:
    import discord
except ImportError as e:
    raise RuntimeError(
        "discord.py package not installed. Run: pip install discord.py"
    ) from e

from app.common.state import PostState
from app.database.db import Database
from app.notify.discord_bot import CUSTOM_ID_PREFIX

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "yakumo.db")


class RevisionModal(discord.ui.Modal, title="YAKUMOへの修正指示"):
    instruction = discord.ui.TextInput(
        label="どう直してほしいか（日本語で簡潔に）",
        style=discord.TextStyle.paragraph,
        max_length=300,
        required=True,
    )

    def __init__(self, db: Database, entry_id: str):
        super().__init__()
        self._db = db
        self._entry_id = entry_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            self._db.transition(
                self._entry_id,
                PostState.REVISION_REQUESTED,
                revision_instruction=str(self.instruction),
            )
        except Exception as e:  # noqa: BLE001 — Discordへ理由を返すため意図的に広く捕捉
            await interaction.response.send_message(
                f"修正指示の保存に失敗しました: {e}", ephemeral=True
            )
            return

        await interaction.response.send_message(
            "修正指示を受け付けました。再生成はまだ自動化されていません "
            "（今後の対応予定）。", ephemeral=True
        )


class YakumoDiscordBot(discord.Client):
    def __init__(self, db: Database, **kwargs):
        intents = discord.Intents.default()
        super().__init__(intents=intents, **kwargs)
        self.db = db

    async def on_ready(self) -> None:
        print(f"[discord_daemon] ログイン完了: {self.user}")

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        parts = custom_id.split(":", 2)

        if len(parts) != 3 or parts[0] != CUSTOM_ID_PREFIX:
            return

        _, action, entry_id = parts

        if action == "approve":
            await self._handle_decision(
                interaction, entry_id, PostState.APPROVED, "approved", "✅ 承認されました"
            )
        elif action == "reject":
            await self._handle_decision(
                interaction,
                entry_id,
                PostState.REJECTED_BY_USER,
                "rejected",
                "❌ 却下されました",
            )
        elif action == "revise":
            await interaction.response.send_modal(RevisionModal(self.db, entry_id))

    async def _handle_decision(
        self,
        interaction: discord.Interaction,
        entry_id: str,
        next_state: PostState,
        approval_status: str,
        result_label: str,
    ) -> None:
        try:
            self.db.transition(entry_id, next_state, approval_status=approval_status)
        except Exception as e:  # noqa: BLE001 — Discordへ理由を返すため意図的に広く捕捉
            await interaction.response.send_message(
                f"状態更新に失敗しました: {e}", ephemeral=True
            )
            return

        await interaction.response.edit_message(
            content=result_label,
            embeds=interaction.message.embeds,
            view=None,
        )


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN not set. "
            "USER ACTION REQUIRED: see docs/credentials.md section 2."
        )

    os.makedirs(DATA_DIR, exist_ok=True)
    db = Database(DB_PATH)

    bot = YakumoDiscordBot(db=db)
    bot.run(token)


if __name__ == "__main__":
    main()
