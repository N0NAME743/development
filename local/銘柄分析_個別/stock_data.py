import pandas as pd
import yfinance as yf
from setup import EXCEL_PATH

def get_symbols_from_excel():
    try:
        df = pd.read_excel(EXCEL_PATH)
        df.columns = df.columns.str.strip().str.lower()
        if "symbol" not in df.columns:
            raise ValueError("❌ 'symbol'列が見つかりません")
        return df["symbol"].dropna().tolist()
    except Exception as e:
        print(f"❌ Excel読み込み失敗: {e}")
        return []

def fetch_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        name = ticker.info.get("shortName", symbol)
        df = ticker.history(period="18mo", interval="1d")
        if df.empty:
            raise ValueError("データが空です")
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).copy()
        return df, name
    except Exception as e:
        print(f"❌ データ取得失敗: {symbol} - {e}")
        return None, symbol
