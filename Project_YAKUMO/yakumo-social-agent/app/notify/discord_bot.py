"""Phase 4: Discord Botによるレビュー通知（送信側）。

送信（このファイル）はDiscordのGatewayへ接続する必要がなく、Bot Tokenを使った
単発のREST API呼び出しだけで完結する（他のプロバイダと同じrequestsベース）。

ボタン（承認/却下/修正）のInteractionを受け取る側は discord_daemon.py（別プロセス、
常駐が必要）が担当する。custom_idの形式 "yakumo:{action}:{source_entry_id}" は
両ファイルで共有している。
"""

from urllib.parse import quote

import requests

from app.common.models import PostCandidate
from app.notify.base import Notifier

DISCORD_API_BASE = "https://discord.com/api/v10"

CUSTOM_ID_PREFIX = "yakumo"


def _x_intent_url(text: str) -> str:
    """X APIを使わず、Web Intent（普通のWebページ）で投稿画面を開くリンク。

    課金なし。本文が入力済みの投稿画面が開くだけで、実際に投稿するかは
    人間が最終確認して自分でポストする（自動投稿の履歴・ペース制御の
    対象外になる代わりに、X API従量課金が一切発生しない）。
    """

    return f"https://x.com/intent/tweet?text={quote(text)}"


def _build_payload(candidate: PostCandidate) -> dict:
    judgement = candidate.ai_judgement

    fields = [
        {
            "name": "元ネタ",
            "value": candidate.source.get("summary") or "(要約なし)",
            "inline": False,
        },
        {
            "name": "投稿案（実際にXへ送る本文。リンクは付与しない）",
            "value": candidate.text or "(本文なし)",
            "inline": False,
        },
        {
            "name": "判定",
            "value": (
                f"テーマ={judgement.topic} / sensitivity={judgement.sensitivity}"
                if judgement
                else "(判定なし)"
            ),
            "inline": False,
        },
    ]

    if candidate.source_url:
        fields.append(
            {
                "name": "元投稿URL（承認/API投稿には含まれません。「Xで開く」には含まれます）",
                "value": candidate.source_url,
                "inline": False,
            }
        )

    embed = {
        "title": "YAKUMO 投稿候補",
        "color": 0xFF4DA6,  # ネオンピンク（Visual Bible準拠）
        "fields": fields,
    }

    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 3,
                    "label": "承認",
                    "custom_id": f"{CUSTOM_ID_PREFIX}:approve:{candidate.source_entry_id}",
                },
                {
                    "type": 2,
                    "style": 4,
                    "label": "却下",
                    "custom_id": f"{CUSTOM_ID_PREFIX}:reject:{candidate.source_entry_id}",
                },
                {
                    "type": 2,
                    "style": 2,
                    "label": "修正",
                    "custom_id": f"{CUSTOM_ID_PREFIX}:revise:{candidate.source_entry_id}",
                },
                {
                    "type": 2,
                    "style": 5,  # Link button。押すとBotを介さず直接このURLを開く
                    "label": "🔗 Xで開く（無課金）",
                    # X API経由の自動投稿（承認）はコスト面でリンクを付けない方針だが、
                    # こちらはAPIを使わない（課金されない）ため、リンクを付けても
                    # コストが変わらない。人間が最終確認して投稿するため、
                    # 元ネタへの導線を残しておいたほうが親切。
                    "url": _x_intent_url(
                        f"{candidate.text}\n{candidate.source_url}"
                        if candidate.source_url
                        else candidate.text
                    ),
                },
            ],
        }
    ]

    return {"embeds": [embed], "components": components}


class DiscordBotNotifier(Notifier):
    def __init__(self, bot_token: str, guild_id: str, channel_id: str):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self._headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json",
        }

    def post_for_review(self, candidate: PostCandidate) -> str:
        response = requests.post(
            f"{DISCORD_API_BASE}/channels/{self.channel_id}/messages",
            headers=self._headers,
            json=_build_payload(candidate),
            timeout=15,
        )
        response.raise_for_status()

        return response.json()["id"]
