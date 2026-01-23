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

            # STEP1：事業内容（文章情報）
            business_description = info.get("longBusinessSummary")

            # STEP3：成長性（量の変化）
            # --- 年次損益計算書（STEP3 用） ---
            revenue_diff = None
            operating_income_diff = None

            try:
                financials = stock.financials

                # 最新2期分が揃っている場合のみ計算
                if financials is not None and financials.shape[1] >= 2:
                    # 売上高の前年差
                    revenue_now = financials.loc["Total Revenue"].iloc[0]
                    revenue_prev = financials.loc["Total Revenue"].iloc[1]
                    revenue_diff = revenue_now - revenue_prev

                    # 営業利益の前年差
                    operating_now = financials.loc["Operating Income"].iloc[0]
                    operating_prev = financials.loc["Operating Income"].iloc[1]
                    operating_income_diff = operating_now - operating_prev

            except Exception:
                # financials が取れない／項目が無い場合は None のまま
                pass

            results.append({
                "ticker": ticker,
                "name": name,
                "date": today,

                # STEP1：事業・規模感
                "business_description": business_description,
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
                "revenue_diff": revenue_diff,
                "operating_income_diff": operating_income_diff,

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
