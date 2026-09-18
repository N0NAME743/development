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

$pricesJson = & python -X utf8 ".\get_yfinance_multi.py" 2>$null
$prices = $pricesJson | ConvertFrom-Json

if (-not $prices -or $prices.Count -eq 0) {
    Write-Error "株価データが取得できませんでした。処理を中断します。"
    exit 1
}

# =========================
# 銘柄ごとに Gemini 実行
# =========================
foreach ($p in $prices) {

    # ベースコードと同じ判定（ここは絶対に変えない）
    if (-not $p.prev_close) {
        Write-Warning "スキップ: $($p.ticker)（価格取得不可）"
        continue
    }

    $ticker = $p.ticker
    $name   = $p.name

    Write-Host "分析中: $ticker $name"

# =========================
# YAML frontmatter（拡張版）
# =========================
$yaml = @"
---
ticker: $ticker
name: $name
date: $Date

business:
  business_description: |
    $($p.business_description)
  market_cap: $($p.market_cap)
  total_revenue: $($p.total_revenue)
  employees: $($p.employees)

price:
  prev_close: $($p.prev_close)

valuation:
  market_cap: $($p.market_cap)
  per: $($p.per)
  pbr: $($p.pbr)
  psr: $($p.psr)
  peg: $($p.peg)

growth:
  revenue_growth: $($p.revenue_growth)
  earnings_growth: $($p.earnings_growth)
  eps_growth: $($p.eps_growth)

financial_health:
  total_assets: $($p.total_assets)
  total_debt: $($p.total_debt)
  equity: $($p.equity)
  debt_to_equity: $($p.debt_to_equity)
  current_ratio: $($p.current_ratio)
  total_cash: $($p.total_cash)

profitability:
  roe: $($p.roe)
  roa: $($p.roa)
  operating_margin: $($p.operating_margin)
  profit_margin: $($p.profit_margin)
  dividend_yield: $($p.dividend_yield)

meta:
  source: $($p.source)

tags:
  - ＠Stock/Fundamental_$name
---
"@

# =========================
# 出力パス
# =========================
$safeName   = $name -replace '[\\/:*?"<>|]', '_'
$outputPath = "$OutputDir\${Date}_${ticker}_${safeName}_fa.md"

# =========================
# YAML を先に書き込む
# =========================
Set-Content $outputPath $yaml -Encoding utf8

# =========================
# プロンプト組み立て（ベース思想維持）
# =========================

$systemPrompt = @"
以下の情報は外部ツールで取得した**確定データ**です。
**記載されている情報のみを使用してください。**
検索・推定・補完・一般論による穴埋めは禁止します。

# STEP1
【事業内容】
$($p.business_description)

【企業規模】
時価総額: $($p.market_cap)
売上高: $($p.total_revenue)
従業員数: $($p.employees)

【株価】
前日終値: $($p.prev_close)

# STEP2
【バリュエーション指標】
PER: $($p.per)
PBR: $($p.pbr)
PSR: $($p.psr)
PEG: $($p.peg)

【評価方針（STEP2）】
・PER は利益が安定している企業でのみ重視する  
・赤字または利益変動が大きい場合、PER は参考外とする  
・PBR は資産型・成熟企業で重視する  
・PSR は成長企業・赤字企業の評価に用いる  
・PEG が 1 前後であれば成長と価格のバランスは良好と判断する  

【注意（STEP2）】
STEP2 の評価は、STEP1 で整理された事業特性および成長フェーズを前提に行ってください。
PER および PEG が算出不能な場合、それ自体を重要な評価情報として扱ってください。

# STEP3
【成長性指標】
売上成長率: $($p.revenue_growth)
利益成長率: $($p.earnings_growth)
EPS成長率: $($p.eps_growth)

【絶対値の変化（前年差）】
売上高前年差: $($p.revenue_diff)
営業利益前年差: $($p.operating_income_diff)

【評価方針（STEP3）】
・STEP3 では、STEP2 で織り込まれている将来期待が、実際の成長数値によって裏付けられているかを検証する  
・最初に売上成長率を確認し、事業需要の拡大有無を判断する  
・利益成長率は、売上成長に遅れてでも改善傾向が見られるかを確認する  
・利益が未成長または赤字であっても、売上成長が明確であれば成長初期フェーズとして許容する  
・売上成長が見られない場合は、期待先行型バリュエーションの正当性に注意を払う  

【注意（STEP3）】
成長率の数値が取得できない場合は、売上高や利益額の絶対値の変化から成長の兆候を検討してください。

# STEP4
【財務健全性指標】
総資産: $($p.total_assets)
総負債: $($p.total_debt)
自己資本: $($p.equity)
負債比率（D/E）: $($p.debt_to_equity)
流動比率: $($p.current_ratio)
現金及び現金同等物: $($p.total_cash)

【評価方針（STEP4）】
・STEP4 では、企業が成長を実現するまでの期間を資金面で耐えられるかを評価する  
・成長初期企業では、利益よりも現金水準と流動性を重視する  
・流動比率が低い場合、短期的な資金繰りリスクに注意を払う  
・負債比率が高い場合、金利上昇や返済負担による経営圧迫を考慮する  
・現金水準と自己資本が十分であれば、成長が遅れても耐久力があると判断する  
・財務的な耐久力が乏しい場合、将来期待があっても投資判断は慎重とする  

【注意（STEP4）】

# STEP5
【総合判断の目的】
STEP1〜STEP4 の分析結果を統合し、
本企業が「投資対象として適切かどうか」を結論づけてください。

【判断区分】
最終判断は、以下のいずれかを必ず明示してください。
・Buy（投資を検討できる）
・Watch（監視・条件付き検討）
・Avoid（現時点では見送り）

【評価方針（STEP5）】
・STEP5 では、新たな情報や推測を加えず、STEP1〜STEP4 の内容のみを根拠として用いる  
・事業の魅力（STEP1）、市場期待の大きさ（STEP2）、成長の裏付け（STEP3）、財務耐久力（STEP4）を総合的に評価する  
・一部に不確実性が残る場合は、その点を明示したうえで慎重な判断とする  
・「なぜ Buy ではないのか」「なぜ Watch に留めるのか」といった判断理由を明確に言語化する  

【最終出力要件】
以下を必ず含めてください。
1. 総合評価の要約（1〜2文）
2. 投資判断（Buy / Watch / Avoid）
3. 判断理由（STEP1〜4 を踏まえた説明）
4. 今後、判断が変わりうる注目ポイント（条件）

【注意（STEP5）】
結論は断定的に述べつつも、不確実性が残る点については慎重な表現を用いてください。

以下は STEP5 の確定判断（YAML）です。

【YAML 出力（STEP5）】
以下の形式で、STEP5 の結論を YAML としても出力してください。
YAML 部分のみをコードブロックで囲ってください。

step5_decision:
  rating: <Buy | Watch | Avoid>
  summary: <総合判断の要約>
  conditions:
    - <判断が変わる条件1>
    - <判断が変わる条件2>
  decided_on: {{DATE}}

【取得元】
$($p.source)
取得日: $Date
"@

$templatePrompt = Get-Content ".\prompt_get_stock_fundamentals_yf.md" -Raw -Encoding utf8

$finalPrompt = $systemPrompt + "`n`n" + $templatePrompt `
    -replace "{{TICKER}}", $ticker `
    -replace "{{NAME}}",   $name `
    -replace "{{DATE}}",   $Date

# =========================
# Gemini 実行（本文をそのまま追記）
# =========================
$finalPrompt |
    gemini generate |
    Add-Content $outputPath -Encoding utf8

Write-Host "→ 出力完了: $outputPath"
}

Write-Host "すべての銘柄の分析が完了しました。"
