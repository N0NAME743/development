import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib
import mplfinance as mpf

from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.trend import ADXIndicator
from ta.momentum import StochasticOscillator
from datetime import datetime

# ✅ 設定
JP_FONT = "IPAexGothic"
EXCEL_PATH = "Symbols.xlsx"

# ✅ フォント設定
plt.rcParams['font.family'] = JP_FONT

# ✅ 銘柄リストを読み込む
EXCEL_PATH = "Symbols.xlsx"  # ← ファイル名に合わせて変更

def get_symbols_from_excel():
    try:
        df = pd.read_excel(EXCEL_PATH)  # ← read_csv ではなく read_excel
        df.columns = df.columns.str.strip().str.lower()  # 小文字＋余白削除
        if "symbol" not in df.columns:
            raise ValueError("❌ 'symbol'列が見つかりません")
        symbols = df["symbol"].dropna().tolist()
        print(f"✅ Excelから読み込み成功: {len(symbols)}銘柄")
        return symbols
    except Exception as e:
        print(f"❌ Excel読み込み失敗: {e}")
        return []

# ✅ 株価取得（yfinance使用）
import yfinance as yf
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

# ✅ 指標追加
def add_indicators(df):
    df["RSI"] = RSIIndicator(df["Close"]).rsi()
    df["MA25"] = df["Close"].rolling(25).mean()
    macd = MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    bb = BollingerBands(df["Close"])
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    adx = ADXIndicator(df["High"], df["Low"], df["Close"])
    df["ADX"] = adx.adx()
    stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
    df["STOCH_K"] = stoch.stoch()
    return df

# ✅ チャート描画・保存
def plot_chart(df, symbol, name):
    df_recent = df.tail(60).copy()
    addplots = [
        mpf.make_addplot(df_recent["MA25"], color="orange"),
        mpf.make_addplot(df_recent["RSI"], panel=1, color='blue'),
        mpf.make_addplot(df_recent["MACD"], panel=2, color='green'),
        mpf.make_addplot(df_recent["MACD_signal"], panel=2, color='red')
    ]
    save_path = f"chart_{symbol}.png"
    mpf.plot(
        df_recent,
        type='candle',
        style='yahoo',
        addplot=addplots,
        title=f"{name} ({symbol}) - 株価チャート",
        ylabel="株価",
        volume=True,
        savefig=save_path
    )
    print(f"📈 保存完了: {save_path}")

# ✅ メイン処理
def main():
    #symbols = get_symbols_from_csv(CSV_PATH)
    symbols = get_symbols_from_excel()
    for symbol in symbols:
        df, name = fetch_stock_data(symbol)
        if df is None:
            continue
        df = add_indicators(df)
        plot_chart(df, symbol, name)

if __name__ == "__main__":
    main()
