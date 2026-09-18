import yfinance as yf
import csv
import json
from datetime import datetime

CSV_PATH = "stocks.csv"

results = []
today = datetime.now().strftime("%Y-%m-%d")

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        ticker = row["ticker"].strip()
        name = row.get("name", "").strip()

        try:
            stock = yf.Ticker(ticker)

            # --- 株価（前日終値） ---
            hist = stock.history(period="2d")
            if hist.empty or len(hist) < 2:
                raise Exception("価格データ不足")

            prev_close = float(hist["Close"].iloc[-2])

            # --- 財務指標 ---
            info = stock.info  # ← ここが追加ポイント

            market_cap = info.get("marketCap")
            per = info.get("trailingPE")
            pbr = info.get("priceToBook")

            results.append({
                "ticker": ticker,
                "name": name,
                "date": today,
                "prev_close": prev_close,
                "market_cap": market_cap,
                "per": per,
                "pbr": pbr,
                "source": "Yahoo Finance (yfinance)"
            })

        except Exception as e:
            results.append({
                "ticker": ticker,
                "name": name,
                "date": today,
                "prev_close": None,
                "market_cap": None,
                "per": None,
                "pbr": None,
                "source": "ERROR",
                "error": str(e)
            })

print(json.dumps(results, ensure_ascii=False, indent=2))
