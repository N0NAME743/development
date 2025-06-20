# ==============================
# Sec｜main.py
# ==============================

import matplotlib.pyplot as plt
from setup import JP_FONT
from stock_data import get_symbols_from_excel, fetch_stock_data
from chart_config import add_indicators, plot_chart

print("📄 このファイルは実行されています:", __file__)

plt.rcParams['font.family'] = JP_FONT

def main():
    symbols = get_symbols_from_excel()
    print(f"✅ Excelから読み込み成功: {len(symbols)}銘柄")  # ← 一元化

    for symbol in symbols:
        print(f"▶ 処理中: {symbol}")
        df, name = fetch_stock_data(symbol)
        if df is None:
            print(f"⚠ データ取得スキップ: {symbol}")
            continue
        df = add_indicators(df)
        plot_chart(df, symbol, name)

if __name__ == "__main__":
    main()
