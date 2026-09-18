# Prompt Polisher

VS Code に打ち込んだ下書きテキストを、生成AI（Claude / ChatGPT など）に渡しやすい
構造化プロンプトへその場で整形する拡張機能。

エディタで整形したいテキストを選択し、コマンド `Prompt Polisher: 選択範囲をプロンプトに整形`
（デフォルトキーバインド: `Ctrl+Alt+P` / macOS: `Cmd+Alt+P`）を実行すると、
選択範囲が整形後のプロンプトに置き換わります。

## 仕組み

- 変換処理は VS Code の [Language Model API](https://code.visualstudio.com/api/extension-guides/language-model)
  (`vscode.lm`) 経由で行われます。追加の API キーは不要ですが、GitHub Copilot Chat など、
  Language Model を提供する拡張機能が有効になっている必要があります。
- 初回実行時に「この拡張機能がモデルを利用してよいか」という VS Code 標準の確認ダイアログが
  表示されます。許可すると以降は確認なしで利用できます。
- 出力フォーマットは「目的 / 背景・前提 / 制約条件 / 期待する出力」の見出しを持つ
  Markdown です。元の文章に無い情報を勝手に補完しないよう指示しています
  （`src/extension.ts` の `SYSTEM_INSTRUCTION` を編集すれば変更できます）。

## セットアップ

```bash
cd tools/prompt-polisher
npm install
npm run compile
```

VS Code でこのフォルダを開き、`F5` で拡張機能開発ホストを起動して動作確認できます。
