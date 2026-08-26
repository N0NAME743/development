
import pandas as pd
import yfinance as yf
import time
import csv
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from datetime import datetime

# 日付フォルダ名を取得（例: '2025-06-24'）
today_str = datetime.now().strftime("%Y-%m-%d")
output_dir = Path(today_str)
output_dir.mkdir(exist_ok=True)  # ← フォルダがなければ作成

# --- 設定 ---
DATA_XLS_PATH = Path("data_j.xls")
RESULT_CSV_PATH = Path("initial_move_candidates.csv")
FETCH_PERIOD = "60d"
MIN_VOLUME = 50000
MAX_WORKERS = 10  # 並列数（PCに合わせて調整）
SMA_SHORT = 5
SMA_LONG = 25
RSI_PERIOD = 14
MAX_RSI = 70

# --- 条件セット（段階的に緩める） ---
CONDITIONS = [
    {"volume_change": 2.0, "price_range": 0.03},
    {"volume_change": 1.5, "price_range": 0.05},
    {"volume_change": 1.2, "price_range": 0.07}
]

# --- ステップ①：銘柄リスト取得（東証プライム） ---
def load_prime_symbols_from_xls(xls_path):
    df = pd.read_excel(xls_path, header=0)
    df.columns = df.columns.str.strip().str.lower()
    if "market" not in df.columns or "code" not in df.columns or "symbol" not in df.columns:
        raise ValueError(f"必要な列（market, code, symbol）が見つかりません。列名一覧: {df.columns.tolist()}")
    df = df[df["market"].str.contains("プライム", na=False)]
    df["code"] = df["code"].astype(str).str.zfill(4) + ".T"
    return df[["code", "symbol"]].drop_duplicates()

# --- ステップ②：初動検知 ---
def calculate_rsi(series, period=RSI_PERIOD):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def detect_initial_move_row(row, vol_threshold, pr_threshold):
    symbol, name = row.code, row.symbol
    try:
        df = yf.download(symbol, period=FETCH_PERIOD, interval="1d", progress=False, auto_adjust=False)
        if df.empty or len(df) < SMA_LONG + RSI_PERIOD:
            return None

        df["volume_change"] = df["Volume"] / df["Volume"].rolling(SMA_SHORT).mean()
        df["price_range"] = (df["Close"] - df["Open"]).abs() / df["Open"]
        df["avg_volume"] = df["Volume"].rolling(SMA_SHORT).mean()
        df["sma_short"] = df["Close"].rolling(SMA_SHORT).mean()
        df["sma_long"] = df["Close"].rolling(SMA_LONG).mean()
        df["rsi"] = calculate_rsi(df["Close"])

        latest = df.iloc[[-1]]
        if (
            latest["volume_change"].iloc[0] > vol_threshold and
            latest["price_range"].iloc[0] < pr_threshold and
            latest["avg_volume"].iloc[0] > MIN_VOLUME and
            latest["Close"].iloc[0] > latest["Open"].iloc[0] and
            latest["Close"].iloc[0] > latest["sma_short"].iloc[0] and
            latest["sma_short"].iloc[0] > latest["sma_long"].iloc[0] and
            latest["rsi"].iloc[0] < MAX_RSI
        ):
            return {
                "symbol": symbol,
                "name": name,
                "date": latest.index[0].strftime("%Y-%m-%d"),
                "open": round(latest["Open"].iloc[0], 2),
                "high": round(latest["High"].iloc[0], 2),
                "low": round(latest["Low"].iloc[0], 2),
                "close": round(latest["Close"].iloc[0], 2),
                "volume_change": round(latest["volume_change"].iloc[0], 2),
                "price_range": round(latest["price_range"].iloc[0], 4),
                "avg_volume": int(latest["avg_volume"].iloc[0]),
                "sma_short": round(latest["sma_short"].iloc[0], 2),
                "sma_long": round(latest["sma_long"].iloc[0], 2),
                "rsi": round(latest["rsi"].iloc[0], 1),
            }
    except Exception:
        return None
    return None

# --- ステップ③：全銘柄ループ処理 ---
def main():
    start = time.time()
    symbols_df = load_prime_symbols_from_xls(DATA_XLS_PATH)
    total = len(symbols_df)
    print(f"📥 全銘柄数: {total}件")

    for idx, condition in enumerate(CONDITIONS, 1):
        vol_th = condition["volume_change"]
        pr_th = condition["price_range"]

        print(f"\n🔍 条件セット {idx}: volume_change > {vol_th}, price_range < {pr_th}")

        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(detect_initial_move_row, row, vol_th, pr_th)
                       for row in symbols_df.itertuples()]
            for i, future in enumerate(as_completed(futures), 1):
                if i % 100 == 0:
                    print(f"🚀 {i}件処理中...")
                result = future.result()
                if result:
                    results.append(result)

        if results:
            condition_info = f"volume_change > {vol_th}, price_range < {pr_th}, MIN_VOLUME > {MIN_VOLUME}"
            output_path = output_dir / f"initial_move_candidates_v{idx}_{today_str}.csv"

            # 条件行付きでCSV出力
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([f"# 条件: volume_change > {vol_th}, price_range < {pr_th}, MIN_VOLUME > {MIN_VOLUME}"])
                results_df = pd.DataFrame(results)
                writer.writerow(results_df.columns)
                writer.writerows(results_df.values)

            print(f"\n✅ 条件セット {idx} にて {len(results)}件検出 → {output_path}")
            break
        else:
            print(f"⛔ 条件セット {idx} は該当なし（volume>{vol_th}, price<{pr_th}）")

    elapsed = time.time() - start
    print(f"\n⏱️ 所要時間: {elapsed:.2f}秒（約{elapsed/60:.1f}分）")

if __name__ == "__main__":
    main()
