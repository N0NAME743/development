chcp 65001 | Out-Null

[System.Globalization.CultureInfo]::DefaultThreadCurrentCulture   = "ja-JP"
[System.Globalization.CultureInfo]::DefaultThreadCurrentUICulture = "ja-JP"

$env:PYTHONIOENCODING = "utf-8"
$env:LANG = "ja_JP.UTF-8"
$env:LC_ALL = "ja_JP.UTF-8"

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$today  = Get-Date -Format "yyyy-MM-dd"
$stocks = Import-Csv .\stocks.csv

# ===== Output Folder =====
$outDir = Join-Path (Get-Location) $today
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

foreach ($row in $stocks) {

    $ticker = $row.name
    $code   = $row.code
    $tickerSafe = $ticker -replace '[\\/:*?"<>|]', '_'

    $mdFile  = Join-Path $outDir "${today}_${tickerSafe}.md"
    $logFile = Join-Path $outDir "${today}_${tickerSafe}_run.log.txt"

    # ===== Logging Header =====
    Set-Content $logFile "MD FILE  : $(Split-Path $mdFile -Leaf)" -Encoding utf8
    Add-Content $logFile "TICKER   : $ticker" -Encoding utf8
    Add-Content $logFile "CODE     : $code" -Encoding utf8
    Add-Content $logFile "----------------------------------------" -Encoding utf8

    # ===== Logging Time =====
    $start = Get-Date
    Add-Content $logFile "START    : $start" -Encoding utf8

    $prompt = Get-Content .\prompt.md -Raw
    $prompt = $prompt -replace "{{TICKER}}", $ticker
    $prompt = $prompt -replace "{{CODE}}",   $code
    $prompt = $prompt -replace "{{TODAY}}",  $today

    $time = Measure-Command {
        $prompt |
          gemini generate |
          Set-Content $mdFile -Encoding utf8
    }

    $end = Get-Date
    Add-Content $logFile "END      : $end" -Encoding utf8
    Add-Content $logFile "DURATION : $($time.TotalSeconds) sec" -Encoding utf8
    Add-Content $logFile "----------------------------------------" -Encoding utf8
}
