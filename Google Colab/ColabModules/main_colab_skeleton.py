# main_colab_skeleton.py
import sys
sys.path.append('/content/drive/MyDrive/ColabModules')

import config as flags
from indicator_calc import calculate_indicators
from plot_chart import plot_stock_chart
from generate_table import make_styled_table

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
today_str = datetime.now(JST).strftime("%Y-%m-%d")

symbols = ["2432.T", "7203.T"]

for symbol in symbols:
    try:
        name = yf.Ticker(symbol).info.get("shortName", "名称不明")
        df = yf.download(symbol, period="15mo", interval="1d")
        df = df.dropna().astype(float)

        df = calculate_indicators(df, flags)
        chart_path = plot_stock_chart(df, symbol, name, flags, today_str)
        styled_table = make_styled_table(df, flags, name, symbol, today_str)

        from IPython.display import HTML, display
        display(HTML(f"<h4>{name}（{symbol}）｜{today_str}</h4>"))
        display(styled_table)

    except Exception as e:
        print(f"❌ {symbol} - {e}")
