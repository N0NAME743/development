#!/usr/bin/env python3
"""Phase 4 デーモン: Discord Botの常駐プロセス（Interaction受信専用）。

poll_inbox.py / process_queue.py は定期実行（数分〜十数分おき）で完結するが、
このプロセスだけはDiscordのボタン操作をリアルタイムで受け取るため常駐が必要
（systemd等でx-likes-notion.serviceのような永続サービスとして動かす想定）。

役割:
  ✅ 承認 → APPROVED（process_queue.pyが投稿ペース制御キューで拾う）
  ❌ 却下 → REJECTED_BY_USER
  ✏️ 修正 → モーダルで指示を受け取り、AIで再生成した新しい投稿案を
            改めてDiscordへ投稿する（WAITING_APPROVALへ戻る）。
            元のメッセージはボタンを外して「修正版を再投稿した」旨に更新する

必要な環境変数（.env。docs/credentials.md 参照）:
  DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, DISCORD_CHANNEL_ID
  AI_PROVIDER, GEMINI_API_KEY 等（修正時の再生成に使うAIProvider。poll_inbox.pyと共用）
"""

import asyncio
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

from app.ai.base import AIProvider
from app.common.factory import build_ai_provider, build_notifier
from app.common.models import PostCandidate
from app.common.state import PostState
from app.database.db import Database
from app.notify.base import Notifier
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

    def __init__(
        self,
        db: Database,
        ai: AIProvider,
        notifier: Notifier,
        entry_id: str,
        original_message: discord.Message,
    ):
        super().__init__()
        self._db = db
        self._ai = ai
        self._notifier = notifier
        self._entry_id = entry_id
        self._original_message = original_message

    async def on_submit(self, interaction: discord.Interaction) -> None:
        instruction_text = str(self.instruction)

        try:
            self._db.transition(
                self._entry_id,
                PostState.REVISION_REQUESTED,
                revision_instruction=instruction_text,
            )
        except Exception as e:  # noqa: BLE001 — Discordへ理由を返すため意図的に広く捕捉
            await interaction.response.send_message(
                f"修正指示の保存に失敗しました: {e}", ephemeral=True
            )
            return

        # AI呼び出しは数秒かかりうるため、先に一旦応答を確定させておく
        # （Discordの3秒以内応答制限を回避するため）。
        await interaction.response.defer(ephemeral=True)

        row = self._db.get(self._entry_id)

        try:
            revised_text = await asyncio.to_thread(
                self._ai.revise,
                row["source_text"] or "",
                row["draft_text"] or "",
                instruction_text,
            )

            review = await asyncio.to_thread(
                self._ai.final_review, row["source_text"] or "", revised_text
            )
            final_text = review.revised_text

            self._db.transition(
                self._entry_id, PostState.DRAFTED, draft_text=final_text
            )

            candidate = PostCandidate(
                source_entry_id=self._entry_id,
                content_hash="",
                text=final_text,
                source_url=row["source_url"],
                source={"summary": (row["source_text"] or "")[:60]},
            )

            new_message_id = self._notifier.post_for_review(candidate)

            self._db.transition(
                self._entry_id,
                PostState.WAITING_APPROVAL,
                discord_message_id=new_message_id,
            )
        except Exception as e:  # noqa: BLE001 — Discordへ理由を返すため意図的に広く捕捉
            self._db.transition(self._entry_id, PostState.FAILED, error_message=str(e))
            await interaction.followup.send(
                f"再生成に失敗しました: {e}", ephemeral=True
            )
            return

        try:
            await self._original_message.edit(
                content="✏️ 修正版を新しいメッセージで再投稿しました（下記参照）",
                embeds=self._original_message.embeds,
                view=None,
            )
        except Exception:
            pass  # 元メッセージの編集に失敗しても、再投稿自体は成功しているので致命的ではない

        await interaction.followup.send(
            f"修正して再投稿しました:\n{final_text}", ephemeral=True
        )


class YakumoDiscordBot(discord.Client):
    def __init__(self, db: Database, ai: AIProvider, notifier: Notifier, **kwargs):
        intents = discord.Intents.default()
        super().__init__(intents=intents, **kwargs)
        self.db = db
        self.ai = ai
        self.notifier = notifier

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
            await interaction.response.send_modal(
                RevisionModal(
                    self.db, self.ai, self.notifier, entry_id, interaction.message
                )
            )

    async def _handle_decision(
        self,
        interaction: discord.Interaction,
        entry_id: str,
        next_state: PostState,
        approval_status: str,
        result_label: str,
    ) -> None:
        # 二重クリックや、前回の承認/却下でDB更新後にメッセージ編集が
        # 反映されなかった場合、ボタンが残ったまま再度押されることがある。
        # その場合は「WAITING_APPROVAL -> next_state」ではなく
        # 「next_state -> next_state」等の不正遷移としてInvalidTransitionに
        # なってしまうため、先に現在の状態を見て素直に済ませる。
        row = self.db.get(entry_id)

        if row is not None and row["state"] != PostState.WAITING_APPROVAL.value:
            await interaction.response.edit_message(
                content="⚠️ この投稿はすでに処理済みです（二重操作を無視しました）",
                embeds=interaction.message.embeds,
                view=None,
            )
            return

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
    ai = build_ai_provider()
    notifier = build_notifier()

    bot = YakumoDiscordBot(db=db, ai=ai, notifier=notifier)
    bot.run(token)


if __name__ == "__main__":
    main()
