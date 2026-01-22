import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import yfinance as yf
import csv
import json
from datetime import datetime

CSV_PATH = "stocks.csv"
today = datetime.now().strftime("%Y-%m-%d")

results = []

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        ticker = row["ticker"].strip()
        name = row.get("name", "").strip()

        try:
            stock = yf.Ticker(ticker)

            # --- 株価 ---
            hist = stock.history(period="2d")
            if hist.empty or len(hist) < 2:
                raise Exception("価格データ不足")
            prev_close = float(hist["Close"].iloc[-2])

            info = stock.info

            results.append({
                "ticker": ticker,
                "name": name,
                "date": today,

                # STEP1：事業・規模感
                "market_cap": info.get("marketCap"),
                "total_revenue": info.get("totalRevenue"),
                "operating_income": info.get("operatingIncome"),
                "net_income": info.get("netIncomeToCommon"),
                "employees": info.get("fullTimeEmployees"),

                # STEP2：バリュエーション
                "per": info.get("trailingPE"),
                "pbr": info.get("priceToBook"),
                "psr": info.get("priceToSalesTrailing12Months"),
                "peg": info.get("pegRatio"),

                # STEP3：成長性
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "eps_growth": info.get("earningsQuarterlyGrowth"),

                # STEP4：財務健全性
                "total_assets": info.get("totalAssets"),
                "total_debt": info.get("totalDebt"),
                "equity": info.get("totalStockholderEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "total_cash": info.get("totalCash"),

                # STEP5：総合判断用
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "operating_margin": info.get("operatingMargins"),
                "profit_margin": info.get("profitMargins"),
                "dividend_yield": info.get("dividendYield"),

                "prev_close": prev_close,
                "source": "Yahoo Finance (yfinance)"
            })

        except Exception as e:
            results.append({
                "ticker": ticker,
                "name": name,
                "date": today,
                "error": str(e),
                "source": "ERROR"
            })

print(json.dumps(results, ensure_ascii=False, indent=2))
