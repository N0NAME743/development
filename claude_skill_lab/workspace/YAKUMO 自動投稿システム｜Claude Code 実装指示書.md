# YAKUMO 自動投稿システム｜Claude Code 実装指示書

あなたはこのプロジェクトの設計・実装を担当するシニアエンジニアです。

以下の要件に基づき、**Day Oneに記録した日記・メモを元に、AIがYAKUMOというキャラクターの投稿文へ変換し、Discordで人間が確認・承認した後にXへ投稿するシステム**を構築してください。

最初から完全自動投稿にはせず、まずは安全な「人間承認あり」の運用を完成させてください。

---

# 1. システムの目的

私がDay Oneに日々記録している文章を素材として、

1. Day Oneから新しい記録を取得
2. 投稿に使える内容か判定
3. YAKUMOというキャラクターの人格・口調へ変換
4. X投稿用の文章を生成
5. Discordへ投稿候補を通知
6. 人間が承認・却下・修正
7. 承認されたものだけXへ投稿
8. 投稿済み情報を記録して重複投稿を防止

という流れを自動化したいです。

最終的なイメージは以下です。

```text
Day One
   ↓
新規エントリー取得
   ↓
投稿候補判定
   ↓
AIによる内容整理
   ↓
YAKUMO人格・口調へ変換
   ↓
X投稿案生成
   ↓
Discord
   ↓
[承認] [却下] [修正]
   ↓
承認された場合のみ
   ↓
Xへ投稿
   ↓
投稿履歴保存
```

---

# 2. YAKUMOの位置付け

YAKUMOは単なる文章変換用の口調ではなく、**継続した人格を持つキャラクター**として扱ってください。

そのため、キャラクター設定をコードやn8nワークフローへ直接ベタ書きせず、独立した設定ファイルとして管理してください。

例：

```text
config/
├── yakumo_profile.md
├── yakumo_writing_rules.md
├── content_policy.md
└── prompts/
    ├── select_content.md
    ├── transform_to_yakumo.md
    └── final_review.md
```

今後、私がYAKUMOの人格・話し方・世界観を調整できる構造にしてください。

---

# 3. YAKUMO用プロンプト設計

AI処理は最低でも以下の3段階に分離してください。

## STEP 1：投稿候補判定

Day Oneの内容を読んで、

- Xに投稿する価値があるか
- 個人的すぎないか
- 機密情報が含まれていないか
- 単なる行動記録だけではないか
- YAKUMOの発言として成立するか

を判定してください。

結果はJSON形式にしてください。

例：

```json
{
  "publishable": true,
  "reason": "AIツールを試した感想として単独投稿にできる",
  "topic": "生成AI",
  "sensitivity": "low"
}
```

---

## STEP 2：YAKUMO変換

投稿可能と判定された内容だけをYAKUMOの人格へ変換してください。

重要なのは、

**原文を単純に言い換えるのではなく、YAKUMOがその出来事を経験したならどう感じ、どう話すか**

という観点で再構成することです。

ただし、原文にない事実を勝手に追加してはいけません。

---

## STEP 3：最終レビュー

生成した投稿について、

- YAKUMOらしさ
- 不自然なAI文章になっていないか
- 長すぎないか
- 説明口調になりすぎていないか
- 原文と意味がズレていないか
- 個人情報・機密情報が残っていないか
- 同じ表現を最近使いすぎていないか

を再確認してください。

問題があれば自動修正してください。

---

# 4. 投稿文の基本方針

YAKUMOの文章は、

- 自然な独り言
- 少し感情がある
- 説明しすぎない
- AIが書いたような定型文を避ける
- 毎回同じ構文を使わない
- 無理に結論を付けない
- 無理に教訓化しない
- ハッシュタグを乱用しない
- 絵文字を乱用しない

という方向を基本にしてください。

投稿は必ずしも140文字以内へ固定せず、Xの現在の仕様とAPI制約を考慮した上で設定可能にしてください。

---

# 5. Discord承認フロー

Discordを「投稿前レビュー画面」として使用します。

Discordには最低限、

```text
YAKUMO 投稿候補

元ネタ:
Day Oneの日記・メモの要約

投稿案:
────────────
生成されたYAKUMO投稿
────────────

判定:
投稿候補 / テーマ / AI confidence
```

を表示してください。

可能であればDiscord Botのボタンを使い、

- ✅ 承認
- ❌ 却下
- ✏️ 修正

を実装してください。

承認時のみX投稿処理へ進んでください。

初期バージョンでは、**Discord承認を経ずにXへ直接投稿する経路は作らないでください。**

---

# 6. 修正フロー

「修正」を選択した場合、

人間がDiscord上から、

```text
もう少し短く
もっとYAKUMOっぽく
この表現を削除
少し皮肉っぽく
```

などの追加指示を送れる仕組みを検討してください。

その指示と元投稿案をAIへ再投入し、改訂版を再度Discordへ提示してください。

---

# 7. 重複投稿防止

同じDay Oneエントリーを複数回処理しないようにしてください。

最低限、

- Day One entry ID
- content hash
- 処理日時
- 投稿候補生成日時
- Discord message ID
- approval status
- X post ID
- X投稿日時

を保存してください。

初期実装ではSQLiteで構いません。

例：

```text
data/
└── yakumo.db
```

将来的にPostgreSQLへ移行可能な構造が望ましいです。

---

# 8. 状態管理

各エントリーは最低限、以下の状態を持たせてください。

```text
NEW
↓
ANALYZED
↓
REJECTED_BY_AI

または

NEW
↓
ANALYZED
↓
DRAFTED
↓
WAITING_APPROVAL
↓
APPROVED
↓
POSTED
```

人間による却下の場合：

```text
WAITING_APPROVAL
↓
REJECTED_BY_USER
```

修正の場合：

```text
WAITING_APPROVAL
↓
REVISION_REQUESTED
↓
DRAFTED
↓
WAITING_APPROVAL
```

---

# 9. n8nの役割

n8nはワークフローのオーケストレーターとして使用してください。

可能なら以下をn8nで管理してください。

```text
定期実行
↓
Day One取得
↓
新規データ判定
↓
AI処理
↓
Discord通知
↓
承認イベント受信
↓
X投稿
↓
DB更新
```

ただし、複雑な処理を無理にn8n Functionノードへ詰め込まず、

- API連携
- 状態管理
- AI処理
- Discord Bot処理

などは必要に応じてPythonまたはNode.jsの小さなサービスへ分離してください。

n8nは「何をどの順番で実行するか」の制御に集中させてください。

---

# 10. 推奨ディレクトリ構成

まず適切な構成を検討してください。

一例：

```text
yakumo-social-agent/
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
│
├── n8n/
│   └── workflows/
│
├── app/
│   ├── dayone/
│   ├── discord/
│   ├── x/
│   ├── ai/
│   ├── database/
│   └── common/
│
├── config/
│   ├── yakumo_profile.md
│   ├── yakumo_writing_rules.md
│   ├── content_policy.md
│   └── prompts/
│
├── data/
│
├── tests/
│
└── docs/
    ├── architecture.md
    ├── setup.md
    └── credentials.md
```

より良い構成があれば変更して構いません。

---

# 11. 認証情報

APIキー・トークン・秘密鍵はコードへ直接書かないでください。

`.env` を利用してください。

`.env.example` だけGit管理してください。

想定：

```env
AI_API_KEY=
DISCORD_BOT_TOKEN=
DISCORD_GUILD_ID=
DISCORD_CHANNEL_ID=

X_CLIENT_ID=
X_CLIENT_SECRET=
X_ACCESS_TOKEN=
X_REFRESH_TOKEN=

DAYONE_...
```

具体的な認証方法は、実際に利用可能なDay One / Discord / X API仕様を確認して設計してください。

私がブラウザ上で手動操作しなければならない部分については、

```text
USER ACTION REQUIRED
```

として明確に止めてください。

認証情報を勝手に作ったり推測したりしないでください。

---

# 12. セキュリティ

特に以下を重視してください。

- APIキーをGitへコミットしない
- Day One原文を不用意にログへ全文出力しない
- X投稿前に必ず人間承認
- 投稿内容から個人情報を除外
- 会社名・取引先・金額・住所などを検出できるようにする
- エラー時に同じ投稿を再送しない
- Discordの操作権限を限定する
- Webhookの認証を行う
- X投稿APIへのリトライで二重投稿しない

---

# 13. ログ

以下をログとして残してください。

- workflow execution ID
- Day One entry ID
- AI判定結果
- draft ID
- Discord message ID
- approval event
- X post ID
- error

ただし、Day One原文やAPIキーはログへ記録しないでください。

---

# 14. AIプロバイダーを交換可能にする

特定のAI APIへ強く依存しない設計にしてください。

例えば、

```text
app/ai/
├── base.py
├── openai_provider.py
├── anthropic_provider.py
└── mock_provider.py
```

のように、

```text
AIProvider
```

という抽象レイヤーを作り、

OpenAI / Anthropicなどを後から切り替えられるようにしてください。

---

# 15. Dry Runモード

非常に重要です。

最初は、

```env
DRY_RUN=true
```

をデフォルトにしてください。

Dry Runでは、

- Day One取得
- AI判定
- YAKUMO投稿生成
- Discord送信

までは実行してよいですが、

**Xへは絶対に投稿しないでください。**

X投稿処理は、

```env
DRY_RUN=false
```

かつDiscord承認済みの場合のみ動作させてください。

---

# 16. テスト

最低限、

- 同一Day One entryの二重処理防止
- AIが投稿不可とした場合
- Discord承認
- Discord却下
- 修正依頼
- X API失敗
- X APIタイムアウト
- 二重クリック
- n8n再実行
- サーバー再起動

を想定したテストを用意してください。

実APIを使わず試せるMockも作ってください。

---

# 17. 将来的な拡張を考慮

初期実装には不要ですが、後から以下を追加できる設計にしてください。

```text
Day One
↓
YAKUMO Content Engine
├── X
├── Threads
├── Bluesky
├── Discord
├── Instagram Caption
└── Blog
```

また、

```text
文章
画像
動画
```

を組み合わせた投稿にも拡張できるようにしてください。

特に将来、

**YAKUMOのキャラクター画像生成**
↓
**投稿内容に合わせた画像生成**
↓
**Discordレビュー**
↓
**Xへ文章＋画像投稿**

へ発展させる可能性があります。

そのため、投稿データモデルには最初から、

```json
{
  "text": "...",
  "media": [],
  "source": {},
  "character": "YAKUMO"
}
```

のような拡張余地を残してください。

---

# 18. 今回の作業手順

いきなり大量に実装せず、以下の順番で進めてください。

## Phase 1：現状確認・設計

まず、

1. このプロジェクトの現在のファイル構成を確認
2. 利用可能なランタイム・Docker環境を確認
3. 要件を整理
4. Day Oneの現実的なデータ取得方式を調査
5. Discord / X APIの接続方式を整理
6. アーキテクチャ案を作成
7. 必要な認証情報一覧を整理

してください。

`docs/architecture.md` に設計を残してください。

---

## Phase 2：Mock版

実API認証なしで、

```text
サンプルDay One JSON
↓
AI Mock
↓
YAKUMO投稿生成Mock
↓
Discord出力Mock
```

まで動く状態を作ってください。

---

## Phase 3：AI接続

AI Providerを実装し、

```text
Day One原文
↓
投稿候補判定
↓
YAKUMO変換
↓
最終レビュー
```

を動かしてください。

---

## Phase 4：Discord

Discord Botまたは適切なWebhook/Interaction方式を実装し、

```text
承認
却下
修正
```

を扱えるようにしてください。

---

## Phase 5：X

最後にX APIを接続してください。

Xへの実投稿は、私が明示的に有効化するまでは禁止してください。

---

# 19. Claude Codeの進め方

実装中に不明点があっても、軽微なものは合理的なデフォルトを採用して進めてください。

ただし、

- 有料契約
- 外部サービスへの登録
- OAuth認証
- APIキー取得
- Xへの実投稿
- 本番環境へのデプロイ
- 既存データ削除

が必要になる地点では勝手に進めず、

```text
USER ACTION REQUIRED
```

として、

1. 何をする必要があるか
2. なぜ必要か
3. 具体的な操作手順
4. 作業後にClaudeへ何を伝えればよいか

を説明してください。

---

# 20. 最初に実行してほしいこと

まずコードを書き始める前に、この要件を基にプロジェクト全体を分析してください。

そのうえで、

1. 推奨アーキテクチャ
2. ディレクトリ構成
3. データフロー
4. 状態遷移
5. 必要な外部API
6. 認証が必要な箇所
7. セキュリティ上の注意点
8. Phase 1〜5の実装計画

を提示してください。

その内容に重大な問題がなければ、**認証情報不要で実装可能な部分からそのまま作業を開始してください。**

設計だけを説明して終了せず、実際にファイルを作成し、Mock版が動作するところまで進めてください。