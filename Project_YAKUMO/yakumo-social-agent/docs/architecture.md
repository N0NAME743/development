# YAKUMO 自動投稿システム — アーキテクチャ設計（Phase 1）

作成日: 2026-09-04
担当: Claude Code（実装指示書に基づく設計・実装）

---

## 1. 現状確認の結果

### 1.1 既存ファイル構成

- `Project_YAKUMO/_text-official/` に、キャラクターの公式設定資料一式が既に存在する。
  - `01_1_YAKUMO_Character_Bible_v1.2.md` — 人格・性格・価値観・世界観・能力・関係性の正解（Authority）
  - `02_1_YAKUMO_X_Prompt_v1.4.md` — X上での口調・投稿方針・チェックリストの正解（Authority）
  - Visual Bible / Costume Registry / HACKING MODE 等 — 画像生成用。今回のテキスト投稿システムでは**対象外**
- `Project_YAKUMO/` 配下にはこれまでコード資産が無く、素材・設定ファイルのみだった。今回が最初のソフトウェア実装になる。
- `claude_skill_lab/`（Skill実験用サンドボックス）に指示書が置かれていたが、ユーザーの判断により実装場所は `Project_YAKUMO/yakumo-social-agent/` とした。

### 1.2 利用可能なランタイム

このセッションの実行環境（devcontainer）で確認できた事実：

| 項目 | 状態 |
| --- | --- |
| Python 3 | 利用可能（3.12、venv使用可） |
| Node.js | **未インストール** |
| Docker / Docker Compose | **未インストール（コマンド自体が存在しない）** |

**結論：この開発環境ではDockerもn8nも実行できない。** そのため、指示書が想定する `docker-compose.yml` / n8nワークフローは**成果物として用意するが、この場では実行・検証できない**。Phase 2のMock版は、Docker/n8n無しでも `python3 run_mock.py` で直接動く形にする。実際の本番稼働（n8n常駐、Discord Bot常駐、スケジュール実行）は、ユーザーが管理する別の実行環境（例: 既存のRaspberry Pi、またはDocker Desktopが動く環境）で行うことになる。

---

## 2. 最重要の技術的課題：Day Oneに公式APIが存在しない

指示書のPhase 1項目4「Day Oneの現実的なデータ取得方式を調査」を行った結果、**これはこのプロジェクト全体の設計に関わる重大な制約**であることが判明した。

### 調査結果

- Day One（Automattic）は、外部からエントリーを**読み取る**ための公式APIを提供していない。
- `dayone` / `dayone2` CLI（macOS版Day Oneに付属）は**エントリーの作成・インポート専用**で、既存エントリーの取得・エクスポートには使えない。
- JSON形式でのエクスポートは存在するが、**アプリ内で人間が手動操作（右クリック→Export、または3点メニュー）する必要があり、スケジュール実行や自動トリガーの対象にできない。**
- IFTTT / Zapier のDay One連携は、いずれも「他アプリの出来事 → Day Oneへ新規エントリー作成」という**一方向**のみ。「Day Oneに新規エントリーが書かれたら外部へ通知する」という、今回必要な方向のトリガーは提供されていない。
- Day One公式フォーラムにも「entry automation用の公開APIが欲しい」という要望スレッドが存在し、2026年時点でも未提供。

### 影響

指示書のフロー図の最初のステップ、

```text
定期実行 → Day One取得 → 新規データ判定
```

は、**「Day One側で新規エントリーが書かれたことを自動検知して取得する」という意味では、現状どの正規手段でも実現できない。**

### 提示する選択肢（USER ACTION REQUIRED相当）

これは認証情報の取得とは別種の、**設計上の意思決定**が必要な箇所のため、実装を先に進めず、ここで選択肢を提示する。

| 案 | 方式 | 自動化の度合い | 制約 |
| --- | --- | --- | --- |
| **A. 手動エクスポート監視** | ユーザーが定期的（例: 毎晩）にDay OneアプリからJSONエクスポートし、指定フォルダに置く。システムはそのフォルダを監視し、新規ファイル内の未処理エントリーを拾う | 半自動（エクスポート操作だけ人間） | 一番簡単・安全。今回のPhase 2 Mockはこの方式を前提に実装した |
| **B. ローカルDay Oneストアの直接読み取り** | Day One for Macがローカルに保持する journal パッケージを、コミュニティ製ツール（例: `dayone-to-obsidian` 系）と同様の方法で直接読む | 完全自動 | **Macでのみ動作**。実行環境をそのMacに置く必要がある。非公式な内部フォーマット依存なのでDay Oneのアップデートで壊れるリスクがある |
| **C. 執筆導線を変える** | Day Oneへ直接書く代わりに、Apple ShortcutsなどでDay Oneへの保存と同時に本システムへも送信する仕組みに変える | 完全自動 | 日記を書く操作そのものを変える必要がある。一番手間だが一番技術的に綺麗 |

**Phase 2のMock版は案Aを前提に実装した**（`app/dayone/json_export_source.py`）。実際にどの案を使うかは、Xへの実接続（Phase 5）を有効化する前に確定させてほしい。

---

## 3. 推奨アーキテクチャ

```text
Day One
  │  (案A: 手動export → フォルダ監視 / 案B・C: 別途決定)
  ▼
app/dayone/*Source          … Day Oneエントリーの取得を抽象化（DayOneSource）
  ▼
app/database/db.py          … SQLiteで状態管理・重複防止（dayone_entry_id + content_hash）
  ▼
app/pipeline/runner.py      … STEP1〜3をオーケストレーション
  │   ├─ STEP1: select_content   (投稿候補判定)
  │   ├─ STEP2: transform_to_yakumo (YAKUMO変換、3案生成)
  │   └─ STEP3: final_review     (最終レビュー・自動修正)
  ▼
app/ai/*Provider            … AIProvider抽象化。Mock / Anthropic / OpenAIを差し替え可能
  ▼
app/notify/*Notifier        … Discord通知を抽象化。Mock(コンソール出力) / 実Discord Bot
  ▼
[人間が承認 / 却下 / 修正]
  ▼
app/x/poster.py             … X投稿。DRY_RUN=trueの間は絶対に実行しない
  ▼
app/database/db.py          … 投稿履歴を記録、状態をPOSTEDへ
```

n8nは、上記の各ステップを定期実行・接続する**オーケストレーター**として後付けする想定（指示書どおり）。ただし複雑なロジック（AI呼び出し、状態管理、Discord Bot処理）はn8n Functionノードに詰め込まず、`app/` 以下のPythonサービスに閉じ込め、n8nからはこれらを呼び出すだけにする。

### なぜPythonか

- ユーザーの既存の類似プロジェクト（Raspberry Pi上の `x_likes_to_notion.py`）が同じ構成（Python + requests + SQLite + .env）で、運用ノウハウが揃っている。
- この開発環境にNode.jsが無く、Pythonのみ利用可能。

---

## 4. ディレクトリ構成

```text
yakumo-social-agent/
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml          # 将来のn8n常駐用（この環境では未検証）
│
├── docs/
│   ├── architecture.md         # 本書
│   ├── setup.md
│   └── credentials.md
│
├── config/
│   ├── yakumo_profile.md       # ../../_text-official/…Character Bible への参照（複製しない）
│   ├── yakumo_writing_rules.md # ../../_text-official/…X Prompt への参照（複製しない）
│   ├── content_policy.md       # 新規作成。投稿可否・機密情報判定の基準
│   └── prompts/
│       ├── select_content.md   # STEP1プロンプト
│       ├── transform_to_yakumo.md # STEP2プロンプト
│       └── final_review.md     # STEP3プロンプト（X Prompt §33のCHECK 1-15を活用）
│
├── app/
│   ├── config_loader.py        # Character Bible / X Prompt / config/*.md を実行時ロード
│   ├── common/
│   │   ├── models.py           # PostCandidate, AIJudgement等のデータモデル
│   │   └── state.py            # 状態遷移（PostState Enum + 遷移バリデーション）
│   ├── dayone/
│   │   ├── base.py             # DayOneSource抽象クラス
│   │   ├── json_export_source.py # 案A: JSONエクスポートフォルダ監視
│   │   └── mock_source.py      # Phase2用サンプルデータ
│   ├── ai/
│   │   ├── base.py             # AIProvider抽象クラス
│   │   ├── mock_provider.py    # 実API不要のダミー応答
│   │   ├── anthropic_provider.py # Phase3で実装（現状スタブ、APIキー未設定で例外）
│   │   └── openai_provider.py    # 同上
│   ├── pipeline/
│   │   └── runner.py           # STEP1→2→3のオーケストレーション
│   ├── notify/
│   │   ├── base.py             # Notifier抽象クラス
│   │   ├── console_notifier.py # Phase2用: ターミナルにDiscord風表示
│   │   └── discord_bot.py      # Phase4で実装（現状スタブ）
│   ├── x/
│   │   └── poster.py           # Phase5で実装。DRY_RUN=falseかつ承認済のみ動作（現状スタブ）
│   └── database/
│       └── db.py               # SQLiteスキーマ・状態更新・重複チェック
│
├── data/                        # yakumo.db（gitignore対象）
├── tests/
│   ├── fixtures/sample_dayone_export.json
│   ├── test_state_machine.py
│   ├── test_dedup.py
│   └── test_pipeline_mock.py
│
└── run_mock.py                  # Phase2エントリーポイント（python3 run_mock.py で即実行可）
```

---

## 5. データフロー・データモデル

投稿1件のデータは、指示書17章の拡張余地を踏まえ、最初から以下の形にする。

```json
{
  "dayone_entry_id": "...",
  "content_hash": "sha256(...)",
  "source": {
    "text": "Day One原文",
    "created_at": "..."
  },
  "character": "YAKUMO",
  "ai_judgement": {"publishable": true, "reason": "...", "topic": "...", "sensitivity": "low"},
  "draft_candidates": ["A案", "B案", "C案"],
  "selected_draft": "...",
  "review": {"ok": true, "issues": [], "revised_text": "..."},
  "text": "最終投稿文",
  "media": [],
  "state": "WAITING_APPROVAL"
}
```

## 6. 状態遷移

指示書8章のとおり実装。加えて、セキュリティ要件13章（同じ投稿を再送しない）を満たすため `FAILED` 状態を追加した。

```text
NEW → ANALYZED → REJECTED_BY_AI
NEW → ANALYZED → DRAFTED → WAITING_APPROVAL → APPROVED → POSTED
WAITING_APPROVAL → REJECTED_BY_USER
WAITING_APPROVAL → REVISION_REQUESTED → DRAFTED → WAITING_APPROVAL
DRAFTED/APPROVED/POSTED操作中の例外 → FAILED（人間が確認するまで自動再送しない）
```

DB (`data/yakumo.db`, SQLite) の `posts` テーブルに、指示書7章の必須項目（dayone_entry_id / content_hash / 処理日時 / 投稿候補生成日時 / discord_message_id / approval_status / x_post_id / x投稿日時）＋ state, error_message, revision_instruction を保持する。`dayone_entry_id` にUNIQUE制約をかけ、重複処理を構造的に防止する。

---

## 7. 必要な外部API・認証情報

| サービス | 用途 | 必要になるPhase | 備考 |
| --- | --- | --- | --- |
| Anthropic または OpenAI API | STEP1〜3のAI処理 | Phase 3 | `AIProvider`抽象化により後から切替可能 |
| Discord Bot Token | 承認フロー通知・ボタン受信 | Phase 4 | Bot作成・招待はUSER ACTION REQUIRED |
| X API (OAuth2, Client ID/Secret, Access/Refresh Token) | 投稿 | Phase 5 | 既存のRaspberry Pi側の実装と同じ認証方式が使える見込み |
| Day One | エントリー取得 | Phase 1〜2から関係 | **公式APIなし。2章の方式選択が必要** |

これらはすべて `.env`（`.env.example`のみgit管理）で読み込む。**このセッションでは一切の登録・キー取得を行っていない。**

---

## 8. セキュリティ上の注意点（指示書12〜13章への対応方針）

- `content_policy.md` にNG基準（個人情報・会社名・取引先・金額・住所等）を明文化し、STEP1のAIプロンプトへ組み込む。加えてコード側にも正規表現ベースの簡易セーフティネット（電話番号・郵便番号・金額パターン等の検出）を`app/common`に用意し、AI判定に加えて二重チェックする。
- ログには `workflow実行ID / dayone_entry_id / AI判定結果 / draft_id / discord_message_id / approval_event / x_post_id / error` のみを出力し、**Day One原文とAPIキーは出力しない**（`config_loader.py`・`db.py`のログ関数で意図的に原文を除外する設計にする）。
- X投稿は `DRY_RUN=true` をデフォルトにし、`false` かつ `approval_status == 'approved'` の場合のみ`x/poster.py`が動作する二重ガードにする。
- X投稿リトライ時は `x_post_id` が既に記録されている場合は再投稿しない（冪等性の担保）。

---

## 9. Phase 1〜5 実装計画

| Phase | 内容 | 本セッションでの扱い |
| --- | --- | --- |
| **Phase 1** | 現状確認・設計（本書） | ✅ 完了 |
| **Phase 2** | Mock版（サンプルDay One JSON → AI Mock → YAKUMO投稿生成Mock → Discord出力Mock） | ✅ 本セッションでそのまま着手・実装（認証不要） |
| **Phase 3** | AI Provider実装、実AI接続 | ⏸ APIキー取得が必要 → USER ACTION REQUIRED |
| **Phase 4** | Discord Bot実装（承認/却下/修正ボタン） | ⏸ Bot作成・招待が必要 → USER ACTION REQUIRED |
| **Phase 5** | X API接続・実投稿 | ⏸ OAuth認証・ユーザーの明示的な有効化が必要 → USER ACTION REQUIRED |

この後、Phase 2（Mock版が実際に動くところまで）を続けて実装する。

---

## 10. 追記（2026-09-04）: 情報源をDay Oneから「記録_Research INBOX」へ変更

上記2章の制約（Day Oneに新規エントリー取得用の公式APIが無い）を踏まえ、ユーザーとの相談の結果、情報源をDay Oneではなく、**既存のX→Notionパイプラインが書き込んでいる「記録_Research INBOX」データベース自体**に変更した。

### 変更の理由

- Day One API問題が根本的に解消する（存在しないAPIを回避する策を講じる必要が無くなる）
- 「記録_Research INBOX」の`AI査定`プロパティ（🟢 IDEA BOXへ / ⚪ 保留 / 🔴 重複 / ⚠️ 取得失敗）を、そのままYAKUMOのリアクション対象フィルターとして再利用できる
- YAKUMOのX Prompt公式設定の投稿ジャンル「A｜電脳観測」（AI・テクノロジー・インターネットへの反応）にそのまま合致する。日記の代弁ではなく、電脳世界からXの話題を見つけてリアクションする、という自然な設計になった
- 取得はポーリング方式（`NotionInboxSource`が`POST /v1/data_sources/{id}/query`を定期実行）とし、既存のRaspberry Pi上のパイプラインと同じパターンを踏襲。Notion Webhook（2026年に追加された新機能）による push型も技術的には可能だが、常時待受サーバーとPiの外部公開が必要になるため見送り、まずはポーリングで運用する

### 実装内容

- `app/source/`: `EntrySource`抽象クラス（旧`DayOneSource`から改名）。`NotionInboxSource`が現在のデフォルト実装。`JSONExportSource`（Day One案A）はコードとして残置（将来の切り戻し用、現在未使用）
- ページ本文の「📝 AI整理メモ」見出し直後の段落（既存パイプラインがGeminiで生成した要約）を、YAKUMOのリアクション元テキストとして使用する。実データ（本番の記録_Research INBOX）で取得テスト済み
- STEP2プロンプト（`config/prompts/transform_to_yakumo.md`）を「日記の代弁」から「YAKUMOがこの情報を見てどう反応するか」という電脳観測フレーミングへ変更

### 文字数予算

Xのリンクは実際の長さに関わらずt.co換算で固定23文字（2026年時点の仕様、無料/Premium共通）。投稿は「YAKUMOの反応本文 + 改行 + 元投稿へのリンク」の構成にするため、AIが生成する本文は280 − 23 − 1 = **256文字以内**（`app/common/text_budget.py`の`REACTION_TEXT_BUDGET`）に収める。X Promptの通常投稿量（1〜5行）を踏まえると十分な余裕があり、実質的な制約にはならない。リンクはAIに書かせず、`PostCandidate.full_post_text()`がシステム側で機械的に付与する。

### 投稿ペース制御（キュー）

既存のX→Notionパイプラインと同様、1回のポーリングで複数件が新規追加されている場合、STEP1〜3の処理・Discord通知は全件同時に行って問題ない（人間が確認するだけのため）。ただし**承認後の実際のX投稿**は、短時間に連投するとキャラクター的に不自然になるため（X Prompt §29 投稿全体のバランス）、`app/pipeline/queue.py`の`PostingQueue`が「前回の実投稿から`MIN_POST_INTERVAL_MINUTES`（既定30分）以上空いているか」をチェックし、承認済みの中で最も古いものから1件ずつ、間隔を空けて投稿する設計にした。

承認はDiscordから即座に行える（Discord Bot自体はPhase 4で未実装）。実際の投稿は`process_queue.py`を数分おきに定期実行することで進む想定（`run_mock.py`の定期取得ジョブとは別プロセス）。DRY_RUN=true の間は、ペース制御のロジック自体は動作確認できるが、DBの状態はAPPROVEDのまま変更しない（DRY_RUN解除後に正しく投稿できるようにするため）。単体テスト（`tests/test_posting_queue.py`）でペース制御・DRY_RUN時の非破壊動作を検証済み。

---

## 11. 追記（2026-09-06）: Phase 4・5を実装し、元投稿へのリンクを廃止

Discord Bot（Phase 4）とX投稿（Phase 5）を実装し、実際のDiscordサーバー・実際のXアカウントで動作確認した。

### X APIの従量課金化への対応

実装・検証の過程で、X APIが2026年2月以降「リンクを含む投稿は$0.20/件、含まない投稿は$0.015/件」という従量課金になっていることが判明した（詳細は`docs/credentials.md` 3章）。当初の設計（9章の文字数予算）は「本文 + 元投稿へのリンク」を前提にしていたが、コスト面からユーザーの判断で**リンクを付けない方針へ変更**した。

- `app/x/poster.py`は`PostCandidate.text`のみを投稿する（リンクを含む`full_post_text()`は削除）
- 文字数予算は280文字（`X_POST_MAX_CHARS`）まるごと使えるようになった（`app/common/text_budget.py`）
- Discord承認画面には引き続き元投稿URLを別フィールドとして表示する（人間が参照・クリックできるように）。ツイート本文には含まれない
- `config/prompts/transform_to_yakumo.md`・`final_review.md`のプロンプトもリンク前提の記述を削除

### X投稿にはtweet.writeスコープの再認可が必要だった

既存の`x_likes_to_notion.py`用のAccess Tokenは読み取り専用スコープ（`tweet.read`等）のみで発行されており、投稿には`tweet.write`が無いため`403 Forbidden`になった。X Developer PortalでApp permissionsを「Read and Write」に変更した上で、OAuth2 Authorization Code + PKCEフローを新たに実行し、`tweet.write`を含むAccess/Refresh Tokenを取得し直した（`yakumo-social-agent/.env`のみ更新。`x_likes_to_notion.py`側の読み取り専用トークンはそのまま）。

### GitHub Trendingを情報源として追加、Discord「修正」ボタンの再生成を実装

`app/source/github_trending_source.py`を追加（GitHub公式Trending APIは存在しないため、Search API `created:>N日前 stars:>=N`で近似）。AIProvider/Notifierの組み立てを`app/common/factory.py`へ共通化し、`poll_github_trending.py`を新規エントリーポイントとして追加。

Discordの「修正」ボタンは、これまで指示をDBに保存するだけで実際の再生成処理が無かった（`REVISION_REQUESTED`のまま誰も処理しない詰み状態だった）。`AIProvider.revise()`（`config/prompts/revise.md`）を追加し、修正指示送信後にAIで再生成 → 新しい投稿案を改めてDiscordへ投稿 → `WAITING_APPROVAL`へ戻す、という一連の流れを実装した。

### 構想メモ（未着手）: X返信投稿でのGitHub実装例の紹介

ユーザーから「GitHubで見つけたリポジトリの実装例・使い方を、YAKUMOの反応投稿へのリプライとして追加投稿できないか」という着想が出た。技術的には難しくないが、以下のピースが新たに必要になるため、着手時は要見積もり:

1. **README等の取得**: `GitHubTrendingSource`は現状メタデータ（名前・説明・スター数）のみ取得しており、実装例・使い方を書くには`GET /repos/{owner}/{repo}/readme`等でREADME本文を別途取得する必要がある
2. **要約用のAIステップ**: README全文は長いため、「使い方」部分を抽出・要約する新しいプロンプト+`AIProvider`メソッドが必要（`revise()`追加時と同程度の工数感）
3. **リプライとして投稿**: X API自体は`in_reply_to_tweet_id`を指定するだけで対応可能（`app/x/poster.py`に追加するだけ）
4. **DBスキーマ拡張**: リプライ本文を保持するカラムが必要
5. **Discord確認UIの拡張**: 本文とリプライ文をまとめて承認できるように`_build_payload`を拡張する必要がある

コスト面: リプライも別の1投稿としてカウントされるため、本文+リプライで**1セットあたり2投稿分**の課金になる。リプライにリポジトリへのリンクを含める場合はそこだけ$0.20（リンクあり）になる。

なお、画像・動画などのメディア添付についても2026年2月以降の従量課金体系での明確な追加コストは确認できていない（$0.015/$0.20の区別はURLの有無によるもので、メディア自体の追加課金は公開情報からは見つからなかった）。実装する場合は`POST /2/media/upload`エンドポイント自体の課金有無をX Developer Portalの最新情報で確認すること。

**長い手順・設定例をどう扱うか（280文字制約への対処案）**

ユーザーとの議論で以下の案が出た。優先度が高い順（軽量な実装ほど優先）:

1. **（推奨・最有力）全部を伝えようとしない**: 手順を網羅的に要約しようとすると中途半端で分かりにくくなる。そうではなく、AIに「一番面白い・意外だった一点だけ」（導入コマンド1行、一番驚いた仕様など）をYAKUMOの口調で拾わせる。実装コストが最も低く、複数投稿の管理も不要
2. **（①の補完）コード部分だけ画像化**: ツイート本文は改行・インデントが崩れるため、短い1行コマンドはテキストのまま、複数行のコード例が必要な場合だけ画像として生成する
3. 無理やり要約してまとめる（①の劣化版、基本的には1のほうが良い）
4. 意味が通るように切り分けて複数のリプライに分割（スレッド化） — 情報量は最大だが、投稿の親子関係の管理・何連投になるか予測しづらい・レート制限やコストに引っかかりやすいなど実装・運用コストが最も重い。**ユーザーの意向として「重い処理・余計な制限がかかる実装は避けたい」ため、優先度は低い**
5. ざっくりした手順全体を1枚の画像にする（②より対象範囲が広い版。検討の余地はあるが実装方法は未検討）

方針: **まずは1（一点だけ抜粋）を軸に、コードがどうしても必要な場面だけ2（コード画像化）を足す**、という軽量な組み合わせを優先する。4のようなスレッド化・重い処理は当面避ける。

**コード画像化（案2）の実装方針**

外部の「綺麗なコード画像」サービス（carbon.now.sh等）は使わない方針とする。第三者サービスへの依存（レート制限・停止リスク・仕様変更）を避けたいという意向のため。

代わりに **Pygments + Pillow** を使う。`pygments.formatters.img.ImageFormatter` がPNGを直接出力できるため、ヘッドレスブラウザ等の重い依存が不要（`pip install pygments pillow`のみ）。ラズパイでも軽く動く。

```python
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import ImageFormatter

def code_to_image(code: str, language: str = "python") -> bytes:
    lexer = get_lexer_by_name(language)
    formatter = ImageFormatter(
        font_name="DejaVu Sans Mono",
        line_numbers=False,
        style="monokai",
    )
    return highlight(code, lexer, formatter)  # PNGのバイト列
```

Xへの添付は `POST /2/media/upload` でPNGをアップロードして`media_id`を取得 → `POST /2/tweets`の`media.media_ids`に指定、という流れになる。

要準備: モノスペースフォント（`DejaVu Sans Mono`等）。多くのLinuxディストリに標準搭載だが、無ければ`apt install fonts-dejavu`で追加。
