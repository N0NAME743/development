# セットアップ

## Phase 2（今すぐ試せる。認証情報不要）

```bash
cd yakumo-social-agent
python3 run_mock.py        # 情報源取得(Mock) → AI判定・生成(Mock) → Discord通知(Mock)
python3 process_queue.py   # 承認シミュレーション → 投稿ペース制御キューの動作確認(DRY_RUN)
```

`data/yakumo.db` が作成され、サンプルの「記録_Research INBOX」エントリー4件が処理される。もう一度`run_mock.py`を実行すると、同じエントリーは重複防止により再処理されない（`data/yakumo.db` を削除すればリセットできる）。

## 実データでの動作確認（NotionInboxSourceを試す場合）

既存のX→Notionパイプラインと同じNotion認証情報があれば、Mockを介さず実際の「記録_Research INBOX」からデータを取得できる（AI/Discord/X部分はまだMockのまま組み合わせて試せる）。`docs/credentials.md` の4章を参照し、`.env`に`NOTION_TOKEN`/`NOTION_DATA_SOURCE_ID`を設定する。

## Phase 3以降

`docs/credentials.md` に必要な認証情報の一覧と取得手順（USER ACTION REQUIRED部分）をまとめている。準備ができたら `.env.example` を `.env` にコピーし、値を埋める。

```bash
cp .env.example .env
```

`.env` は絶対にgitへコミットしないこと（`.gitignore` 済み）。
