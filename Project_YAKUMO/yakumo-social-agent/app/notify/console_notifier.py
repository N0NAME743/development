"""Phase 2用: Discordの代わりにターミナルへ指示書5章のフォーマットで表示する。"""

import itertools

from app.common.models import PostCandidate
from app.notify.base import Notifier

_ids = itertools.count(1)


class ConsoleNotifier(Notifier):
    def post_for_review(self, candidate: PostCandidate) -> str:
        message_id = f"mock-discord-{next(_ids)}"

        judgement = candidate.ai_judgement

        print("=" * 60)
        print("YAKUMO 投稿候補  [MOCK DISCORD MESSAGE]")
        print()
        print("元ネタ:")
        print(f"  {candidate.source.get('summary', '(要約なし)')}")
        print()
        print("投稿案（実際にXへ送る本文。リンクは機械的に付与）:")
        print("-" * 20)
        for line in candidate.full_post_text().splitlines():
            print(f"  {line}")
        print("-" * 20)
        print(f"  文字数（リンクはt.co換算23文字で計算）: {len(candidate.text)}文字 + リンク")
        print()
        print(
            f"判定: 投稿候補={judgement.publishable} / "
            f"テーマ={judgement.topic} / sensitivity={judgement.sensitivity}"
        )
        print()
        print("[承認]  [却下]  [修正]   (Phase 4でDiscord Botのボタンとして実装予定)")
        print("=" * 60)

        return message_id
