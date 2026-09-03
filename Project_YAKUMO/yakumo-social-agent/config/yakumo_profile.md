# YAKUMO Profile（設定ファイル）

このファイルはYAKUMOの人格を**再定義しない**。

YAKUMOの人格・性格・価値観・世界観・能力・MONYとの関係性の唯一の正解（Authority）は、

```text
../../_text-official/01_1_YAKUMO_Character_Bible_v1.2.md
```

である。

`app/config_loader.py` は、実行のたびにこのCharacter Bibleを上記パスから直接読み込む。ここに内容を複製しないのは、Character Bibleが更新されたときに本システムが自動的に最新版へ追従するようにするため（複製すると、本家が更新されてもこちらが古いままになる事故が起きる）。

## 参照優先順位（Character Bible §16.1に準拠）

1. `01_1_YAKUMO_Character_Bible_v1.2.md` — 人格・性格・価値観・世界観・能力・関係性
2. `02_1_YAKUMO_X_Prompt_v1.4.md`（→ `yakumo_writing_rules.md`）— X上での実行ルール

## Character Bibleを更新したとき

このファイルは何も変更しなくてよい。Character Bibleのファイル名・バージョンが変わる場合（例: v1.2 → v1.3）のみ、上記パスとルート直下の `docs/credentials.md` の参照表を更新すること。
