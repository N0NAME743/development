import yfinance as yf
import json
from datetime import datetime

# === 設定 ===
ticker = "7203.T"  # トヨタ

stock = yf.Ticker(ticker)
hist = stock.history(period="2d")

if hist.empty or len(hist) < 2:
    raise Exception("価格データ取得不可")

data = {
    "ticker": ticker,
    "date": datetime.now().strftime("%Y-%m-%d"),
    "prev_close": float(hist["Close"].iloc[-2]),
    "source": "Yahoo Finance (yfinance)"
}

print(json.dumps(data, ensure_ascii=False))
