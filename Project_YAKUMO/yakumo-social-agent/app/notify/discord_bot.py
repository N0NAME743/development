"""Phase 4: Discord Botによるレビュー通知（送信側）。

送信（このファイル）はDiscordのGatewayへ接続する必要がなく、Bot Tokenを使った
単発のREST API呼び出しだけで完結する（他のプロバイダと同じrequestsベース）。

ボタン（承認/却下/修正）のInteractionを受け取る側は discord_daemon.py（別プロセス、
常駐が必要）が担当する。custom_idの形式 "yakumo:{action}:{source_entry_id}" は
両ファイルで共有している。
"""

import json
from urllib.parse import quote

import requests

from app.common.code_image import code_to_image, first_code_image
from app.common.models import PostCandidate
from app.notify.base import Notifier

DISCORD_API_BASE = "https://discord.com/api/v10"

CUSTOM_ID_PREFIX = "yakumo"


def _x_intent_url(text: str, source_url: str | None = None) -> str:
    """X APIを使わず、Web Intent（普通のWebページ）で投稿画面を開くリンク。

    課金なし。本文が入力済みの投稿画面が開くだけで、実際に投稿するかは
    人間が最終確認して自分でポストする（自動投稿の履歴・ペース制御の
    対象外になる代わりに、X API従量課金が一切発生しない）。

    DiscordのリンクボタンURLは512文字までという制限があり、日本語は
    パーセントエンコードで1文字が最大9文字に膨らむため、通常の長さの
    投稿案でもすぐ超過してクラッシュしていた（本文が空でも
    Discordの400 Bad Requestで投稿候補自体が届かなくなる致命的なバグ）。
    超える場合は本文側だけを切り詰める。source_urlは切り詰めない
    （リンク先が壊れると参照する意味が無いため）。
    """

    prefix = "https://x.com/intent/tweet?text="
    max_len = 512
    ellipsis = "…"

    suffix = f"\n{source_url}" if source_url else ""
    budget = max_len - len(prefix) - len(quote(suffix))

    if len(quote(text)) <= budget:
        return prefix + quote(text + suffix)

    ellipsis_len = len(quote(ellipsis))
    body = text

    while body and len(quote(body)) + ellipsis_len > budget:
        body = body[:-1]

    return prefix + quote(body + ellipsis + suffix)


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

    code_image = first_code_image(candidate.media)

    if code_image is not None:
        lines = code_image["code"].count("\n") + 1
        fields.append(
            {
                "name": "🖼 添付コード画像（承認時にXへも添付されます）",
                "value": f"{code_image['language']}（{lines}行）",
                "inline": False,
            }
        )

    embed = {
        "title": "YAKUMO 投稿候補",
        "color": 0xFF4DA6,  # ネオンピンク（Visual Bible準拠）
        "fields": fields,
    }

    if code_image is not None:
        # post_for_review()側でこのファイル名でアップロードする
        # （Discordの添付ファイル参照方式: attachment://<filename>）。
        embed["image"] = {"url": "attachment://code.png"}

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
                    "url": _x_intent_url(candidate.text, candidate.source_url),
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
        payload = _build_payload(candidate)
        code_image = first_code_image(candidate.media)

        if code_image is None:
            response = requests.post(
                f"{DISCORD_API_BASE}/channels/{self.channel_id}/messages",
                headers=self._headers,
                json=payload,
                timeout=15,
            )
        else:
            # 添付ファイル付きメッセージはJSON単体では送れないため、
            # multipart/form-data（payload_json + files）で送る。
            image_bytes = code_to_image(code_image["code"], code_image["language"])

            response = requests.post(
                f"{DISCORD_API_BASE}/channels/{self.channel_id}/messages",
                headers={"Authorization": self._headers["Authorization"]},
                data={"payload_json": json.dumps(payload)},
                files={"files[0]": ("code.png", image_bytes, "image/png")},
                timeout=15,
            )

        response.raise_for_status()

        return response.json()["id"]

    def notify_posted(self, text: str) -> None:
        response = requests.post(
            f"{DISCORD_API_BASE}/channels/{self.channel_id}/messages",
            headers=self._headers,
            json={"content": text},
            timeout=15,
        )
        response.raise_for_status()
