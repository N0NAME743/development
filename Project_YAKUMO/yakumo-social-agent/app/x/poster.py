"""Phase 5で実装するX投稿（未実装スタブ）。

USER ACTION REQUIRED（着手前に必要な作業）:
1. X Developer Portalでアプリを作成し、OAuth2 (Client ID/Secret) を取得する
2. ユーザー自身のアカウントでOAuth2認可を行い、Access/Refresh Tokenを取得する
   （既存のRaspberry Pi上のx_likes_to_notion.pyと同じ認証方式が使える見込み）
3. 取得した値を.envの X_CLIENT_ID / X_CLIENT_SECRET / X_ACCESS_TOKEN / X_REFRESH_TOKEN に設定する
4. 作業後、Tokenの値自体をClaudeに貼らず、.envへ設定済みであることだけ伝える

安全装置（実装時に必ず維持すること。指示書15章・12章）:
- DRY_RUN=true がデフォルト。この間は絶対に実際の投稿を行わない
- DRY_RUN=false かつ approval_status == 'approved' の場合のみ投稿処理へ進む
- 投稿前に x_post_id が既に記録されていないか確認し、二重投稿を防ぐ
- リトライ時も同様のチェックを行う
"""

import os

from app.common.models import PostCandidate


class XPoster:
    def __init__(self):
        self.dry_run = os.getenv("DRY_RUN", "true").lower() != "false"

    def post(self, candidate: PostCandidate) -> str:
        if self.dry_run:
            print(f"[DRY_RUN] Xへは投稿しません: {candidate.text[:40]}...")
            return "dry-run-no-post"

        raise NotImplementedError(
            "Phase 5未実装。USER ACTION REQUIRED: X API認証情報の取得が先に必要。"
            "本ファイルのモジュールdocstringを参照。"
        )
