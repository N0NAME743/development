# 認証情報一覧（USER ACTION REQUIRED）

Claude Codeは以下を代行できない。取得後、値そのものをチャットへ貼らず、「.envへ設定した」とだけ伝えてほしい。

## 1. AI Provider（Phase 3で必要）

- Anthropic Console（https://console.anthropic.com/）または OpenAI Platform（https://platform.openai.com/）でAPIキーを発行
- `.env` の `ANTHROPIC_API_KEY` または `OPENAI_API_KEY`（`AI_API_KEY` でも可）に設定

## 2. Discord Bot（Phase 4で必要）

1. https://discord.com/developers/applications で新規Application作成
2. Bot設定からTokenを発行
3. 対象サーバーへBotを招待（権限: メッセージ送信、Embed送信、ボタンInteraction）
4. `.env` の `DISCORD_BOT_TOKEN` / `DISCORD_GUILD_ID` / `DISCORD_CHANNEL_ID` に設定

## 3. X API（Phase 5で必要）

1. X Developer Portalでアプリを作成し、OAuth2 Client ID/Secretを取得
2. ユーザー自身のアカウントでOAuth2認可フローを実行し、Access Token/Refresh Tokenを取得
   （既存のRaspberry Pi上の `x_likes_to_notion.py` と同じ認証方式が使える見込み。そちらの`.env`設定を参考にできる）
3. `.env` の `X_CLIENT_ID` / `X_CLIENT_SECRET` / `X_ACCESS_TOKEN` / `X_REFRESH_TOKEN` に設定
4. 準備ができても `DRY_RUN=true` のままにしておき、実際にXへ投稿してよいと判断した時点で明示的に `false` へ変更する

## 4. Notion（情報源。docs/architecture.md 10章の変更により、実質すぐ必要）

- 既存のX→Notionパイプライン（`claude_skill_lab/workspace/x_pipeline/.env` やPi上の `x-likes-notion/.env`）と同じ`NOTION_TOKEN` / `NOTION_DATA_SOURCE_ID`が使える
- `.env` の `NOTION_TOKEN` / `NOTION_DATA_SOURCE_ID` に設定（既存の値を流用可）
- `NOTION_AI_HANTEI_VALUE`（既定「🟢 IDEA BOXへ」）は、Notion側の`AI査定`プロパティの選択肢とそのまま一致している必要がある

## 5. Day One（現在は不使用。docs/architecture.md 10章の理由により、情報源を記録_Research INBOXへ変更済み）

- `JSONExportSource`はコードとして残してあるが、現在のデフォルトでは使われていない
- 将来Day Oneへ戻したくなった場合のみ、この章の対応が必要になる
