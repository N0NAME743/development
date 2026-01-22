# 文字コードをUTF-8に固定（PS 5.1 対策）
chcp 65001 | Out-Null

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
[Console]::InputEncoding  = $utf8
$OutputEncoding           = $utf8   # 外部コマンドのパイプ入出力に効くことがある

$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# Python側もUTF-8固定（強力）
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# =========================
# 設定
# =========================

$Date = Get-Date -Format "yyyy-MM-dd"
$OutputDir = ".\$Date"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# =========================
# 株価取得（Python）
# =========================

$prices = & python -X utf8 ".\get_yfinance_multi.py" | ConvertFrom-Json


if (-not $prices -or $prices.Count -eq 0) {
    Write-Error "株価データが取得できませんでした。処理を中断します。"
    exit 1
}

# =========================
# 銘柄ごとに Gemini 実行
# =========================

foreach ($p in $prices) {

    # 株価が取れなかった銘柄はスキップ
    if (-not $p.prev_close) {
        Write-Warning "スキップ: $($p.ticker)（価格取得不可）"
        continue
    }

    $ticker = $p.ticker
    $name   = $p.name
    $price  = $p.prev_close
    $source = $p.source

    Write-Host "分析中: $ticker $name"

    # =========================
    # プロンプト組み立て
    # =========================

    $systemPrompt = @"
以下の数値は外部ツールで取得した確定データです。
株価などの数値は、以下に与えた情報のみを使用してください。
検索・推定・補完は禁止します。

前日の終値: $price
取得元: $source
取得日: $Date
"@

    $templatePrompt = Get-Content ".\prompt.md" -Raw -Encoding utf8

    $finalPrompt = $systemPrompt + "`n`n" + $templatePrompt `
        -replace "{{TICKER}}", $ticker `
        -replace "{{NAME}}",   $name `
        -replace "{{TODAY}}",  $Date `
        -replace "{{DATE}}",   $Date

    # =========================
    # Gemini 実行
    # =========================

    $safeName = $name -replace '[\\/:*?"<>|]', '_'
    $outputPath = "$OutputDir\${Date}_${ticker}_${safeName}_analysis.md"

    $finalPrompt |
        gemini generate |
        Out-File $outputPath -Encoding utf8

    Write-Host "→ 出力完了: $outputPath"
}

Write-Host "すべての銘柄の分析が完了しました。"
