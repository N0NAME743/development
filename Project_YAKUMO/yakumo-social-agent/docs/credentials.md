# 認証情報一覧（USER ACTION REQUIRED）

Claude Codeは以下を代行できない。取得後、値そのものをチャットへ貼らず、「.envへ設定した」とだけ伝えてほしい。

## 1. AI Provider（Phase 3で必要）

3つの実装（`GeminiProvider` / `AnthropicProvider` / `OpenAIProvider`）から選べる。**おすすめはGemini**（無料枠あり・既存キーを流用可）。

- **Gemini（推奨）**: 既存のRaspberry Pi上の `x_likes_to_notion.py` と同じ `GEMINI_API_KEY` がそのまま使える（新規取得不要）。`.env` の `GEMINI_API_KEY`（`AI_API_KEY` でも可）に設定。`gemini-3.5-flash-lite` は無料枠があり、この用途（短文の判定・生成）なら実質無料〜低コストで運用できる見込み
- **Anthropic**: Anthropic Console（https://console.anthropic.com/）でAPIキーを発行し、`.env` の `ANTHROPIC_API_KEY`（`AI_API_KEY` でも可）に設定。無料枠なし
- **OpenAI**: OpenAI Platform（https://platform.openai.com/）でAPIキーを発行し、`.env` の `OPENAI_API_KEY`（`AI_API_KEY` でも可）に設定。無料枠なし

## 2. Discord Bot（Phase 4で必要）

1. https://discord.com/developers/applications で新規Application作成
2. 「Bot」設定からTokenを発行
3. 「OAuth2」→「URL Generator」で scope: `bot`、権限: `Send Messages` / `Embed Links` を選び、生成されたURLで対象サーバーへBotを招待
4. 開発者モードでチャンネルID・サーバーIDを取得
5. `.env` の `DISCORD_BOT_TOKEN` / `DISCORD_GUILD_ID` / `DISCORD_CHANNEL_ID` に設定
6. `pip install discord.py` を実行（`requirements.txt`には含めていない。他のAI providerパッケージと同じく、実際に使う場合だけ追加で入れる方針）
7. `.env`設定後、`poll_inbox.py`は自動的に`DiscordBotNotifier`（Discordへ実送信）に切り替わる。ボタン（承認/却下/修正）を受け取るには `python3 discord_daemon.py` を別プロセスとして常駐させる必要がある（既存のx-likes-notion.serviceと同様、systemdサービス化を推奨）
8. `修正`ボタンは指示をDB（`revision_instruction`）へ保存するところまで実装済み。実際にAIで再生成する自動化はまだ未実装（今後の課題）

## 3. X API（Phase 5で必要。実装済み・実投稿は未検証）

`app/x/poster.py` は実装済み。既存のRaspberry Pi上の `x_likes_to_notion.py` と同じOAuth2認証方式（Access Token期限切れ時の自動リフレッシュ含む）をそのまま使う。

1. `x_likes_to_notion.py`と同じX APIアプリ（OAuth2 Client ID/Secret）・同じユーザーのAccess/Refresh Tokenが流用できる
2. `.env` の `X_CLIENT_ID` / `X_CLIENT_SECRET` / `X_ACCESS_TOKEN` / `X_REFRESH_TOKEN` に設定（既存の値をコピー可）
3. 準備ができても `DRY_RUN=true` のままにしておき、実際にXへ投稿してよいと判断した時点で明示的に `false` へ変更する
4. **X APIは2026年2月以降、投稿1件ごとに従量課金**（リンク無し$0.015、リンクあり$0.20）。YAKUMOの投稿は必ずリンク付きなので1投稿$0.20の計算になる。想定投稿頻度に応じたコストを事前に見積もっておくこと

## 4. Notion（情報源。docs/architecture.md 10章の変更により、実質すぐ必要）

- 既存のX→Notionパイプライン（`claude_skill_lab/workspace/x_pipeline/.env` やPi上の `x-likes-notion/.env`）と同じ`NOTION_TOKEN` / `NOTION_DATA_SOURCE_ID`が使える
- `.env` の `NOTION_TOKEN` / `NOTION_DATA_SOURCE_ID` に設定（既存の値を流用可）
- `NOTION_AI_HANTEI_VALUE`（既定「🟢 IDEA BOXへ」）は、Notion側の`AI査定`プロパティの選択肢とそのまま一致している必要がある

## 5. Day One（現在は不使用。docs/architecture.md 10章の理由により、情報源を記録_Research INBOXへ変更済み）

- `JSONExportSource`はコードとして残してあるが、現在のデフォルトでは使われていない
- 将来Day Oneへ戻したくなった場合のみ、この章の対応が必要になる
