

# 事前準備

## ターミナルを「Power Shell 7」に対応させる

### パソコン上での操作
- ターミナル（管理者権限）で起動
    winget install --id Microsoft.PowerShell -s winget
- ターミナルのプロファイルを切り替え
    Windows Terminal を起動
    右上「▼」→ 設定
    スタートアップ
    既定のプロファイル
    → PowerShell（pwsh）
    保存 → Terminal を再起動

### VSCodeでの操作
- VSCodeのターミナル（PowerShell）を「PowerShell 7」にする
  winget install Microsoft.PowerShell
- 確認
    Get-ChildItem "C:\Program Files\PowerShell\7\pwsh.exe"
    & "C:\Program Files\PowerShell\7\pwsh.exe" --version
- Pathに登録
    １．方法１
        $path = [Environment]::GetEnvironmentVariable("Path","Machine")
    if ($path -notlike "*PowerShell\7*") {
        [Environment]::SetEnvironmentVariable(
            "Path",
            $path + ";C:\Program Files\PowerShell\7\",
            "Machine"
        )
    }
    ２．方法２
        ・Jsonの書き換え
    Ctrl + Shift + P
    Open User Settings (JSON)
    ・Jsonファイルの編集
    {
    "workbench.colorTheme": "Solarized Light",
    "workbench.editorAssociations": {
        "*.copilotmd": "vscode.markdown.preview.editor",
        "*.xlsx": "cweijan.officeViewer"
    },
    "workbench.iconTheme": "office-material-icon-theme",
    "security.allowedUNCHosts": [
        "RPI3MB"
    ],

    "terminal.integrated.profiles.windows": {
        "PowerShell 7": {
        "path": "C:\\Program Files\\PowerShell\\7\\pwsh.exe"
        },
        "Command Prompt": {
        "path": [
            "${env:windir}\\Sysnative\\cmd.exe",
            "${env:windir}\\System32\\cmd.exe"
        ],
        "args": [],
        "icon": "terminal-cmd"
        },
        "Git Bash": {
        "source": "Git Bash",
        "icon": "terminal-git-bash"
        }
    },

    "terminal.integrated.defaultProfile.windows": "PowerShell 7"
    }
- 確認コマンド
  pwsh --version
    7.1バージョンが表示されればオッケー

## VSCodeで「yfinance」を利用できるようにする
- 確認
    python --version
- インストール
    python -m pip install yfinance

# 実行ファイル構成

## 構成

- 株式情報を取得
    [get_yfinance_multi.py]
            ↓（JSON）
    [get_stock_info_yf.ps1]
    ├─ 数値YAML生成
    ├─ Markdown骨組み生成
    ├─ systemPrompt生成
            ↓
    [Gemini]
    └─ STEP1〜5 本文のみ出力
            ↓
    [get_stock_info_yf.ps1]
    └─ 各STEPに本文を差し込み
            ↓
    [完成Markdown]

- 株式分析（ファンダメンタル）を取得

# その他
STEP	役割
-
STEP1	何をやっている会社か
STEP2	市場は何を期待しているか
STEP3	その期待は数字で本当か
STEP4	その途中で倒れないか
STEP5	総合判断

scores:
  step1_business: 2
  step2_valuation: 1
  step3_growth: 2
  step4_financial: 2
  step5_total: 7