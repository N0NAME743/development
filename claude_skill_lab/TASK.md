# claude_skill_lab 引き継ぎ

更新日: 2026-09-18

## 目的

VS Codeを共通の作業場所にして、Claude CodeとCodex（GPT-6 Astra）を使い分ける。上部にClaude Artifactやダッシュボード、下部にClaude Code用ターミナル、右側にCodexを配置し、Dev Containerに接続して作業する。

この資料は、別のCodexアプリの会話から引き継ぐために作成した。会話履歴そのものはVS CodeのCodexやClaude Codeに自動共有されない。両者には、このファイルを明示的に読ませる。

## 作業場所

- Windows: `C:\Users\cran4p\Documents\development\claude_skill_lab`
- Dev Container: `/workspaces/development/claude_skill_lab`
- このファイルの配置先: 上記プロジェクト直下（README.mdと同じ場所）

調査時のGitリポジトリルートは `/workspaces/development` だった。claude_skill_labだけがリポジトリ全体だと仮定しない。変更・コミット前に現在のGitルートと差分を確認し、他の作業を巻き込まない。

## 対象外の並行プロジェクト（このTASK.mdの範囲外）

同じGitルート配下に、このTASK.mdが扱うVS Code/Dev Container運用構築とは無関係な、別プロジェクトが未追跡のまま存在する。誤って本資料の作業と混同・巻き込みしないよう記録する。いずれも削除・移動・コミットの方針は未決定。

- `android/ShareFormatter/`: Android共有シート/テキスト選択メニューで受け取ったテキストをClaude APIでMarkdownに整形し、`.md`/`.html`として再共有するAndroidアプリのスキャフォールド（Kotlin + Jetpack Compose）。このDev ContainerにはAndroid SDK/Gradleが無く、一度もビルド検証されていない。
- ~~`tools/prompt-polisher/`: 選択テキストをVS CodeのLanguage Model API経由で構造化プロンプトに整形するVS Code拡張機能。~~ 2026-09-18、コミット済み（`97e9384`）。`package.json`が`"private": true` / `"publisher": "local"`で公開意図が無い個人用ツールと判断し、他の個人プロジェクトと同様にこのリポジトリで管理する方針にした。`node_modules`/`out`/`*.vsix`は既存の`.gitignore`で除外済み。

## 未整理のGit状態（要確認・未対応）

2026-09-18時点で見つかった、本資料の作業とは別に残っている状態。方針は未決定。

- ~~`/workspaces/development/.claude/worktrees/calm-exploring-umbrella`: 正規のGit worktree。ブランチ`worktree-calm-exploring-umbrella`は`origin`にpush済みで、直近コミットは「tools/prompt-polisher に CLAUDE.md を追加」。mainには未マージ。~~ 2026-09-18、`tools/prompt-polisher`本体のコミット（`97e9384`）後にmainへマージ済み（競合なし）。その後`git worktree remove`でworktreeディレクトリを削除し、ローカル・リモート（`origin/worktree-calm-exploring-umbrella`）双方のブランチも削除済み。完了。
- ~~`claude_skill_lab/CLAUDE.md`（直下）: 中身が0行の空ファイル。~~ 2026-09-18、他ファイルからの参照が無いことを確認の上、削除済み（未追跡ファイルだったためGit履歴には影響なし）。

## 確認済みの環境

以下は調査時点の情報。実際の作業前に必要な範囲で再確認する。

- VS Code 1.138.0
- Dockerの接続先表示: desktop-linux
- Dev Container: Ubuntu 24.04、Node.js 18.20.8
- Claude Code CLI導入済み。調査時にはプロセス稼働を確認した
- 調査時のClaude Code拡張: anthropic.claude-code 2.1.274
- コンテナーの作業ユーザー: vscode
- Project_YAKUMOの追加マウント先: `/workspaces/project-yakumo`
- 同じプロジェクトについて複数のリモート接続URIの保存記録がある。画面復元のため、同じDev Containerの同じフォルダーを開く運用に統一する

## 完了したこと

### 1. 既存環境の読み取り調査

調査時、プロジェクトの `.vscode/settings.json` と `.vscode/tasks.json` は存在しなかった。Documents/development配下に `*.code-workspace` は見つからず、フォルダーを直接開く構成だった。

`.devcontainer/devcontainer.json` には以下が設定されていた。

- Ubuntu 24.04のベースイメージ
- Node.js 18のFeature
- Project_YAKUMOの追加マウント
- postCreateCommandによるClaude Code導入、ダッシュボード用エイリアス登録、SSH設定

### 2. 復元用設定の追加

別のCodexアプリ側では対象への書き込みが許可されなかったため、適用用スクリプトを作成し、ユーザーがWindowsのPowerShellから実行した。初回は成功した。2回目の「Already exists」は意図した上書き防止で、再適用は不要。

追加した `.vscode/settings.json` の内容:

```json
{
  "terminal.integrated.enablePersistentSessions": true,
  "workbench.panel.defaultLocation": "bottom",
  "workbench.browser.newTabPlacement": "activeGroup"
}
```

追加した `.vscode/tasks.json` の概要:

- タスク名: `Claude Sessions: ensure dashboard`
- type: process、command: node
- 引数: `${workspaceFolder}/tools/start-session-dashboard.cjs`
- 作業場所: `${workspaceFolder}`
- runOptions: runOn = folderOpen、instanceLimit = 1
- presentation: reveal = silent、focus = false、panel = dedicated
- problemMatcher: 空配列
- 自動実行にはVS Codeの自動タスク許可が関係する

追加した `tools/start-session-dashboard.cjs` の動作:

- Linux側で実行するための起動補助
- localhost:4756の応答を確認し、Claude Sessionsのタイトルを持つ既存サーバーがあれば再利用
- 別サービスが応答する場合は停止せずエラーにする
- 未起動なら既存の `tools/session-dashboard.js` を `--no-open --port=4756` で起動
- ブラウザーを勝手に追加で開かない
- アプリ固有の厳密な識別APIやOSロックによる判定ではない。競合時はポートの排他と終了後の再確認を利用している

`.devcontainer/devcontainer.json` には `forwardPorts` の4756を追加した。既存のフック・マウント・Featureを保持した。JSONの再出力で整形は変わり得る。

バックアップはプロジェクト内の `.restore-settings-backup/<実行日時>/devcontainer.json` に作成された。初回成功時にユーザーが提示したディレクトリ名は `20260918-085138-513`。正確な場所は実ファイルを確認する。

適用スクリプトはコピー環境で、設定追加、既存設定保持、JSON解析、上書き防止を検証済み。起動補助は構文確認済みだが、あらゆる異常系の動作試験までは行っていない。

### 3. VS Codeを閉じて開き直した結果

ユーザーが自分でVS Codeを終了し、再度開いた。提示されたスクリーンショットで以下を確認した。

- Dev Containerに再接続済み
- 上部にClaude SessionsとArtifactのタブが残っていた
- ダッシュボードが表示された
- 下部ターミナルと右側のChatパネルが復元された
- ターミナル一覧にダッシュボードのタスク名が表示された

画面だけでは、ダッシュボードが新規起動したのか、以前のプロセスを再利用したのかは区別できない。停止したコンテナーやPC再起動からの復旧までは検証していない。

### 4. VS CodeのCodex導入とAstraの確認

ユーザーがOpenAI公式拡張 `openai.chatgpt`（Codex）を追加し、右側にCodexパネルを配置した。

スクリーンショットで `GPT-6 Astra 軽` が選択されていることを確認した。以下の読み取り依頼に正常な回答が得られた。

> 現在の作業ディレクトリを確認し、claude_skill_labのREADMEを読んで、プロジェクトの概要を日本語で説明してください。ファイルの変更やインストールはしないでください。

Codexは `/workspaces/development/claude_skill_lab` を作業場所として報告し、READMEの内容に基づいてskills、repos、workspaceの用途を説明した。変更やインストールはしていないと報告した。

これにより、VS CodeのAstraから対象プロジェクトを読み取れることを確認できた。編集・テスト実行などの権限はまだこの確認では検証していない。認証方式や拡張の配置先の詳細は、画面だけでは確定していない。

## ダッシュボードについて

- `tools/session-dashboard.js` はWebサーバー型。単なるターミナル表示ツールではない
- 標準URL: `http://localhost:4756/`
- `~/.claude/projects` 配下のClaude Codeログを読み、セッション一覧を表示する
- `--no-open` と `--port=` に対応
- `ccdash` はこのスクリプトを起動する既存エイリアス
- 表示対象はClaude Codeの履歴。Codexの履歴が自動で統合される構成ではない
- 元のスクリプト本体は今回変更していない

## 現在の運用

- 上部: Artifact、Claude Sessions、必要なコードファイル
- 下部: ターミナル。Claude Codeを使うときは `claude` を実行
- 右側: CodexでGPT-6 Astraを利用
- 同じファイルに対する編集は、まず一方が完了してからもう一方に渡す
- 例: Claude Codeで実装し、Astraに変更差分をレビューしてもらう
- 引き継ぐときは目的、変更内容、未解決事項をこの資料に追記する

## 未対応・未検証

- Claude Codeの自動起動および特定会話の自動再開
- コンテナー再構築後のClaude Code履歴・認証の保持
  - 調査時点のマウントには `/home/vscode/.claude` の永続化指定がなかった
  - 永続化を追加する際は既存データを移行し、空のマウントで見えなくしない
- 停止したDockerやPC再起動からの完全自動復旧
- Artifactのログイン期限切れからの復帰
- 固定URLを毎回強制的に開く処理、画面の幅や高さを強制する処理
- Claude CodeとCodexの自動ルーティング・自動フェイルオーバー
  - 以前の会話で構想として言及されたが、今回実装した機能ではない
  - 2026-09-18、判定ロジックの構想メモ（未実装・未検証）:
    - 「軽い/重い」を事前に精密分類しようとせず、まず安価/無料モデルに投げて失敗シグナルで上位モデルへ回すエスカレーション式にする
    - 入口フィルタ: 差分行数・対象ファイル数・「設計」「全体」等のキーワードで明らかに重いと判定できた場合のみ、安価モデルを飛ばして最初から上位モデルへ直行
    - エスカレーション条件: モデル自身が「できない/自信がない」と回答／機械的検証（テスト・lint・ビルド等）がNG／タイムアウトやレート制限／一定回数リトライしても改善しない、のいずれか
    - エスカレーション時は安価モデルの出力・エラーを上位モデルへのコンテキストとして引き継ぎ、やり直しにしない
    - 拡張候補: エスカレーション履歴をログして入口フィルタの閾値を後からチューニングできるようにする
- TASK.mdの自動更新や会話履歴の同期

次の候補として提案されたが、実際には適用していないもの:

- ユーザー設定の `window.restoreWindows: "all"`
- Dev Container設定へのClaude Code/Codex拡張の明示的な追加
- ブラウザーの保存方式変更
- `.code-workspace` の新規作成
- postStartCommandやpostAttachCommandへの起動処理追加

## 次の担当への指示

1. まずこの資料と実際の設定を読み、相違があれば報告する。
2. この資料を読むことだけを理由に、追加の実装・インストール・再起動を始めない。
3. ユーザーは既存環境を維持した段階的な変更を希望している。再起動・再構築・プロセス停止は必要性を説明し、その時点のユーザーの指示に従う。
4. `Apply-RestoreSettings.ps1` は初回適用済み。既存設定を削除して再実行しない。必要な変更は現在のファイルに対する最小限のマージで行う。
5. 未コミットの変更や他プロジェクトのファイルを上書き・破棄しない。
6. 次に何を追加するかは未決定。現状は両AIをVS Codeで使う準備ができた段階。

## 参照

- Codex IDE公式資料: https://learn.chatgpt.com/docs/codex/ide
- Codex対応モデル: https://learn.chatgpt.com/docs/models
- VS Codeターミナル復元: https://code.visualstudio.com/docs/terminal/advanced
- VS Code自動タスク: https://code.visualstudio.com/docs/debugtest/tasks
- VS Code内蔵ブラウザー: https://code.visualstudio.com/docs/debugtest/integrated-browser

## 作業記録の追記欄

今後は作業の区切りで、実施日・担当AI・変更ファイル・確認結果・残作業を追記する。確認していない内容は完了扱いにしない。

### 2026-09-18 Claude Code

- 変更ファイル: `start-session-dashboard.cjs`（プロジェクト直下）を削除
- 確認結果: プロジェクト直下と`tools/`配下に内容が完全一致する`start-session-dashboard.cjs`が重複していた。`.vscode/tasks.json`が参照するのは`tools/start-session-dashboard.cjs`のみで、ファイル内部も`path.join(__dirname, 'session-dashboard.js')`という自ディレクトリ基準の参照になっており、`tools/session-dashboard.js`と対で動作する設計だった。直下版を単独実行すると`session-dashboard.js`が見つからず壊れるため、直下版を不要な複製と判断し削除した。
- 残作業: `tools/start-session-dashboard.cjs`の動作は変更していない。他にも`android/ShareFormatter/`や`tools/prompt-polisher/`などTASK.mdに未記載の未追跡ディレクトリがあり、扱いは未決定のまま。

### 2026-09-18 Claude Code（続き・Gitルート `/workspaces/development` 直下の整理）

このセクションのみ、対象は`claude_skill_lab`ではなくGitルート`/workspaces/development`直下全体。ユーザーが「ルートに雑多なフォルダが並んでいるのを整理したい」と依頼したため実施。

- 変更内容（コミット順）:
  - `tools/prompt-polisher/`をコミット（`97e9384`。`"private": true`の個人用VS Code拡張と判断）
  - 既存worktreeブランチ`worktree-calm-exploring-umbrella`（`tools/prompt-polisher/CLAUDE.md`追加）をmainへマージ後、worktree・ローカル/リモートブランチを削除
  - 空の`claude_skill_lab/CLAUDE.md`を削除（参照なしを確認済み）
  - 株分析系4フォルダ（`Google Colab`、`gemini_Cli`、`local`、ルート`銘柄分析_初動`）を`投資関連/`→のちに`investment/`へ統合・改名（`e75dd6a`→`e872568`）
  - `docker_desktop`（空のdevcontainerスキャフォールド）を削除。`docker_desktop_home`は中身を精査し、実制作物（LINEスタンプ申請一式→`line_stickers/`、メモ→ルート、写真3点→`picture/`）を救出した上で、ブラウザ保存キャッシュ（`logs/X.htm`等）と空の設定を削除（`95240ed`）
  - `python_code/`を削除。`_backup/development_20260805/python_code`と`diff -rq`でバイト一致することを確認済み（`ba571ee`）
  - ルート直下に散らばっていた`xcrawler`・`line_stickers`・`popup.vbs`・個人メモを`apps/`・`personal/`にまとめ、`施行履歴.txt`を`history.txt`にリネーム（`9428c90`→`e872568`）
- 確認結果（要注意点）:
  - `_backup/development_20260118`と`development_20260805`は**単純な重複ではない**。`diff -rq`で実際に検証したところ、`local/銘柄分析_個別`配下は両時点で異なるファイル・異なる内容を含む別々の履歴スナップショットだった。誤って片方を削除候補にしないこと。
  - `clients/`の「1093件中11件しか追跡されていない」ように見えた状態は異常ではなく、残りはすべて`.venv/`（`.gitignore`済み）。対応不要。
  - `Project_YAKUMO`は活発に開発中の大規模プロジェクト（228M、直近数日〜2週間以内のコミットあり）。独立リポジトリ化の候補だが、ユーザーの指示で今回は保留。
- 残作業:
  - `Project_YAKUMO`の独立リポジトリ化は未着手（ユーザーが保留を選択）。
  - `apps/xcrawler`内の`test/`と`xcrawler-web/`の内容差分整理は未着手。
  - `android/ShareFormatter/`（claude_skill_lab内、対象外の並行プロジェクト節を参照）は今回も保留のまま。
  - `claude_skill_lab`と`Project_YAKUMO`はdevcontainerのマウントパス等が依存するため、フォルダ名の統一対象から意図的に除外している。
