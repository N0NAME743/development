"""Phase 4で実装するDiscord Bot連携（未実装スタブ）。

USER ACTION REQUIRED（着手前に必要な作業）:
1. Discord Developer Portal (https://discord.com/developers/applications) でBotを作成する
2. Bot Tokenを取得し、.envの DISCORD_BOT_TOKEN に設定する
3. Botをサーバーへ招待し（メッセージ送信・ボタンInteraction権限）、
   DISCORD_GUILD_ID / DISCORD_CHANNEL_ID を.envに設定する
4. 作業後、取得したToken/IDをClaudeに直接貼らず、.envへ設定済みであることだけ伝える

実装方針（Phase 4着手時）:
- discord.py（または pycord）でBotプロセスを常駐させる
- ✅ 承認 / ❌ 却下 / ✏️ 修正 のボタン付きメッセージを送信する（指示書5章）
- ボタンのInteractionを受け取り、app.database.db.Database.transition() で状態を更新する
- 「修正」選択時はモーダル等で追加指示を受け取り、指示書6章の再生成フローへ渡す
"""

from app.common.models import PostCandidate
from app.notify.base import Notifier


class DiscordBotNotifier(Notifier):
    def __init__(self, bot_token: str, guild_id: str, channel_id: str):
        raise NotImplementedError(
            "Phase 4未実装。USER ACTION REQUIRED: Discord Bot作成・招待が先に必要。"
            "本ファイルのモジュールdocstringを参照。"
        )

    def post_for_review(self, candidate: PostCandidate) -> str:
        raise NotImplementedError
