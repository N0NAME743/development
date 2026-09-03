# YAKUMO 自動投稿システム

Xでいいねした投稿（「記録_Research INBOX」に貯まったもの）を、YAKUMOが電脳世界から見つけたリアクションとしてX投稿文へ変換し、Discordでの人間承認を経てからXへ投稿するシステム。

```text
記録_Research INBOX（🟢 IDEA BOXへ判定分）
   ↓
投稿候補判定 → YAKUMO変換 → 最終レビュー
   ↓
Discord承認
   ↓
投稿ペース制御キュー（連投防止）
   ↓
X投稿（本文 + 元投稿へのリンク） → 履歴保存
```

キャラクター設定そのものはこのリポジトリに置かない。唯一の正解（Authority）は常に:

- `../_text-official/01_1_YAKUMO_Character_Bible_v1.2.md`
- `../_text-official/02_1_YAKUMO_X_Prompt_v1.4.md`

情報源として当初Day Oneを検討したが、公式APIが存在しないため「記録_Research INBOX」（既存のX→Notionパイプラインの出力）へ変更した。経緯は `docs/architecture.md` 10章。

## 現在の状態

- **Phase 1（設計）**: 完了 — `docs/architecture.md`
- **Phase 2（Mock版）**: 完了 — `python3 run_mock.py` / `python3 process_queue.py` で実行可能
- **Phase 3〜5**: 未着手（認証情報の取得が必要。`docs/credentials.md` 参照）

## クイックスタート

```bash
python3 run_mock.py        # 情報源取得 → AI判定・生成 → Discord通知（すべてMock）
python3 process_queue.py   # 承認シミュレーション → 投稿ペース制御キューの動作確認
```

詳細は `docs/setup.md`。
