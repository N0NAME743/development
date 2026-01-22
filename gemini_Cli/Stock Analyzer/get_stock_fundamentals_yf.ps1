# =========================
# UTF-8 固定（PS 5.1 対策）
# =========================
chcp 65001 | Out-Null

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
[Console]::InputEncoding  = $utf8
$OutputEncoding           = $utf8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONWARNINGS = "ignore"

# =========================
# 設定
# =========================
$Date = Get-Date -Format "yyyy-MM-dd"
$OutputDir = ".\$Date"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# スクリプト基準パス（安全）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptDir ".\get_yfinance_multi.py"
$PromptFile   = Join-Path $ScriptDir "prompt_get_stock_fundamentals_yf.md"

# =========================
# yfinance 取得（Python）
# =========================
$prices = & python -X utf8 $PythonScript | ConvertFrom-Json
if (-not $prices -or $prices.Count -eq 0) {
    Write-Error "株価データが取得できませんでした。"
    exit 1
}

# =========================
# 銘柄ごと処理
# =========================
foreach ($p in $prices) {

    if (-not $p.prev_close) {
        Write-Warning "スキップ: $($p.ticker)（価格取得不可）"
        continue
    }

    $ticker = $p.ticker
    $name   = $p.name

    Write-Host "分析中: $ticker $name"

    # =========================
    # YAML frontmatter
    # =========================
    $yaml = @"
---
ticker: $ticker
name: $name
date: $Date

price:
  prev_close: $($p.prev_close)

step1_business_scale:
  market_cap: $($p.market_cap)
  total_revenue: $($p.total_revenue)
  operating_income: $($p.operating_income)
  net_income: $($p.net_income)
  employees: $($p.employees)

step2_valuation:
  per: $($p.per)
  pbr: $($p.pbr)
  psr: $($p.psr)
  peg: $($p.peg)

step3_growth:
  revenue_growth: $($p.revenue_growth)
  earnings_growth: $($p.earnings_growth)
  eps_growth: $($p.eps_growth)

step4_financial_health:
  total_assets: $($p.total_assets)
  total_debt: $($p.total_debt)
  equity: $($p.equity)
  debt_to_equity: $($p.debt_to_equity)
  current_ratio: $($p.current_ratio)
  total_cash: $($p.total_cash)

step5_profitability:
  roe: $($p.roe)
  roa: $($p.roa)
  operating_margin: $($p.operating_margin)
  profit_margin: $($p.profit_margin)
  dividend_yield: $($p.dividend_yield)

meta:
  data_source: "$($p.source)"
  fetched_date: $Date
---
"@

    # =========================
    # Markdown 骨組み
    # =========================
    $mdSkeleton = @"
$yaml

## STEP1｜事業・規模感

## STEP2｜バリュエーション評価

## STEP3｜成長性評価

## STEP4｜財務健全性評価

## STEP5｜総合投資判断
"@

    $safeName   = $name -replace '[\\/:*?"<>|]', '_'
    $outputPath = "$OutputDir\${Date}_${ticker}_${safeName}_fa.md"

    Set-Content $outputPath $mdSkeleton -Encoding utf8

    # =========================
    # Gemini 実行
    # =========================

$yamlForPrompt = $yaml   # さっき作った YAML 文字列

$templatePrompt = Get-Content $PromptFile -Raw -Encoding utf8

$finalPrompt = @"
$templatePrompt

────────────────────
以下は分析対象銘柄の YAML frontmatter です。
この YAML に記載された情報のみを用いて分析してください。

$yamlForPrompt
"@

    Write-Host "→ Gemini 実行中..."

    $aiOutput = $finalPrompt | gemini generate

    if (-not $aiOutput) {
        Write-Warning "AI 出力が空でした: $ticker"
        continue
    }

    # =========================
    # STEP 分割
    # =========================
    $steps = @{
    1 = ($aiOutput -split "STEP1:")[1] -split "STEP2:" | Select-Object -First 1
    2 = ($aiOutput -split "STEP2:")[1] -split "STEP3:" | Select-Object -First 1
    3 = ($aiOutput -split "STEP3:")[1] -split "STEP4:" | Select-Object -First 1
    4 = ($aiOutput -split "STEP4:")[1] -split "STEP5:" | Select-Object -First 1
    5 = ($aiOutput -split "STEP5:")[1]
}

    if ($steps.Count -lt 5) {
        Write-Warning "STEP 出力数不足: $ticker"
        continue
    }

    # =========================
    # Markdown 差し込み
    # =========================
    $md = Get-Content $outputPath -Raw -Encoding utf8

    $md = $md `
      -replace "## STEP1｜事業・規模感", "## STEP1｜事業・規模感`n$($steps[1].Trim())" `
      -replace "## STEP2｜バリュエーション評価", "## STEP2｜バリュエーション評価`n$($steps[2].Trim())" `
      -replace "## STEP3｜成長性評価", "## STEP3｜成長性評価`n$($steps[3].Trim())" `
      -replace "## STEP4｜財務健全性評価", "## STEP4｜財務健全性評価`n$($steps[4].Trim())" `
      -replace "## STEP5｜総合投資判断", "## STEP5｜総合投資判断`n$($steps[5].Trim())"
 
    Set-Content $outputPath $md -Encoding utf8

    Write-Host "→ 完成: $outputPath"
}

Write-Host "すべての銘柄の分析が完了しました。"
