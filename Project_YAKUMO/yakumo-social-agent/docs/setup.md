# セットアップ

## 依存パッケージのインストール

```bash
cd yakumo-social-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt        # 実行に必要な最小限（requests, python-dotenv）
pip install -r requirements-dev.txt    # テストも実行する場合（上記 + pytest）
```

## Phase 2（今すぐ試せる。認証情報不要）

```bash
python3 run_mock.py        # 情報源取得(Mock) → AI判定・生成(Mock) → Discord通知(Mock)
python3 process_queue.py   # 承認シミュレーション → 投稿ペース制御キューの動作確認(DRY_RUN)
```

`data/yakumo.db` が作成され、サンプルの「記録_Research INBOX」エントリー4件が処理される。もう一度`run_mock.py`を実行すると、同じエントリーは重複防止により再処理されない（`data/yakumo.db` を削除すればリセットできる）。

## Phase 3（実データ・実AI。GEMINI_API_KEYがあればすぐ試せる）

`docs/credentials.md` に必要な認証情報の一覧と取得手順（USER ACTION REQUIRED部分）をまとめている。準備ができたら `.env.example` を `.env` にコピーし、値を埋める。

```bash
cp .env.example .env
```

`.env` は絶対にgitへコミットしないこと（`.gitignore` 済み）。`run_mock.py` / `process_queue.py` / `poll_inbox.py` はいずれも起動時に`python-dotenv`で`.env`を自動読み込みするため、値を埋めるだけでよい（別途`export`する必要はない）。

最低限必要なのは `NOTION_TOKEN` / `NOTION_DATA_SOURCE_ID`（既存のX→Notionパイプラインと共用可）と、AIプロバイダのキー（既定は無料枠のある `GEMINI_API_KEY`。同じくx_likes_to_notion.pyと共用可）。

```bash
python3 poll_inbox.py      # 実際の記録_Research INBOX → 実AI（既定Gemini）→ Discord通知（まだConsole表示）
python3 process_queue.py   # 承認シミュレーション → 投稿ペース制御キューの動作確認(DRY_RUN)
```

`AI_PROVIDER=anthropic` または `AI_PROVIDER=openai` で切り替え可能（それぞれ対応するAPIキーが必要）。

## Phase 4以降

Discord Bot（承認フロー）とX投稿はまだ未実装。必要な認証情報は `docs/credentials.md` の2・3章を参照。
