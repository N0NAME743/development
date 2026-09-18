# =========================
# UTF-8 固定（PS 5.1 対策）
# =========================
chcp 65001 | Out-Null

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
[Console]::InputEncoding  = $utf8
$OutputEncoding           = $utf8

$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

# Python 側も UTF-8 固定
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

    $ticker     = $p.ticker
    $name       = $p.name
    $price      = $p.prev_close
    $marketCap  = $p.market_cap
    $per        = $p.per
    $pbr        = $p.pbr
    $source     = $p.source

    Write-Host "分析中: $ticker $name"

    # =========================
    # YAML frontmatter 生成
    # =========================
    $yaml = @"
---
ticker: $ticker
name: $name
date: $Date
price:
  prev_close: $price
valuation:
  market_cap: $marketCap
  per: $per
  pbr: $pbr
source: $source
---
"@

    # =========================
    # プロンプト組み立て
    # =========================
    $systemPrompt = @"
以下の数値は外部ツールで取得した確定データです。
**記載されている数値のみを使用してください。**
検索・推定・補完・一般論による穴埋めは禁止します。

【株価情報】
前日の終値: $price

【バリュエーション指標】
時価総額: $marketCap
PER（実績）: $per
PBR: $pbr

【取得情報】
取得元: $source
取得日: $Date
"@

    $templatePrompt = Get-Content ".\prompt_get_stock_info_yf.md" -Raw -Encoding utf8

    $finalPrompt = $systemPrompt + "`n`n" + $templatePrompt `
        -replace "{{TICKER}}", $ticker `
        -replace "{{NAME}}",   $name `
        -replace "{{TODAY}}",  $Date `
        -replace "{{DATE}}",   $Date

    # =========================
    # 出力パス
    # =========================
    $safeName   = $name -replace '[\\/:*?"<>|]', '_'
    $outputPath = "$OutputDir\${Date}_${ticker}_${safeName}_analysis.md"
    $logPath    = "$OutputDir\${Date}_${ticker}_${safeName}.log.txt"

    # =========================
    # YAML を先に書き込む
    # =========================
    Set-Content $outputPath $yaml -Encoding utf8

    # =========================
    # ログ初期化
    # =========================
    Set-Content $logPath "MD FILE  : ${Date}_${ticker}_${safeName}_info.md" -Encoding utf8
    Add-Content $logPath "TICKER   : $ticker" -Encoding utf8
    Add-Content $logPath "NAME     : $name"   -Encoding utf8
    Add-Content $logPath "PRICE    : $price"  -Encoding utf8
    Add-Content $logPath "SOURCE   : $source" -Encoding utf8
    Add-Content $logPath "----------------------------------------" -Encoding utf8

    $start = Get-Date
    Add-Content $logPath "START    : $start" -Encoding utf8

    # =========================
    # Gemini 実行（本文追記）
    # =========================
    $time = Measure-Command {
        $finalPrompt |
            gemini generate |
            Add-Content $outputPath -Encoding utf8
    }

    $end = Get-Date
    Add-Content $logPath "END      : $end" -Encoding utf8
    Add-Content $logPath ("DURATION : {0:N2} sec" -f $time.TotalSeconds) -Encoding utf8
    Add-Content $logPath "----------------------------------------" -Encoding utf8

    Write-Host "→ 出力完了: $outputPath"
    Write-Host "→ ログ完了: $logPath"
}

Write-Host "すべての銘柄の分析が完了しました。"
