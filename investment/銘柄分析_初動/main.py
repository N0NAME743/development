
import argparse
import os
import pandas as pd
import yfinance as yf
import time
import csv
import random
import io
import contextlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from datetime import datetime

# 実行方法
## python main.py --- 通常候補抽出
## python main.py --simulate-symbol 3964.T --signal-date 2026-08-01

# 日付フォルダ名を取得（例: '2025-06-24'）
today_str = datetime.now().strftime("%Y-%m-%d")
output_dir = Path(today_str)
output_dir.mkdir(exist_ok=True)  # ← フォルダがなければ作成

# --- 設定 ---
DATA_XLS_PATH = Path("data_j.xls")
RESULT_CSV_PATH = Path("initial_move_candidates.csv")
FETCH_PERIOD = "90d"
MIN_VOLUME = 50000
MAX_WORKERS = 10  # 並列数（PCに合わせて調整）
SMA_SHORT = 5
SMA_LONG = 25
SMA_MID = 75
RSI_PERIOD = 14
ATR_PERIOD = 14
BB_PERIOD = 20
MEDIAN_VOLUME_PERIOD = 20
MIN_PRICE_RANGE = 0.01
MAX_RSI = 65
MAX_BB_WIDTH = 0.08
MIN_SCORE = 7
MIN_CANDIDATES = 20
TOP_FALLBACK_CANDIDATES = 20
CACHE_DIR = Path("cache")
CACHE_TTL_HOURS = 24
BATCH_SIZE = 50

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


def calculate_atr(df, period=ATR_PERIOD):
    high_low = df["High"] - df["Low"]
    high_prev_close = (df["High"] - df["Close"].shift(1)).abs()
    low_prev_close = (df["Low"] - df["Close"].shift(1)).abs()
    tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def fetch_price_data(symbol, retries=2, delay=1.0):
    for attempt in range(1, retries + 1):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                df = yf.download(symbol, period=FETCH_PERIOD, interval="1d", progress=False, auto_adjust=False, threads=False)
            if df is not None and not df.empty:
                return df

            with contextlib.redirect_stderr(io.StringIO()):
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=FETCH_PERIOD, interval="1d", auto_adjust=False)
            if df is not None and not df.empty:
                return df
            return None
        except Exception:
            if attempt == retries:
                return None
            time.sleep(delay)
    return None


def cache_path(symbol):
    return CACHE_DIR / f"{symbol}.pkl"


def is_cache_valid(path):
    if not path.exists():
        return False
    age = datetime.now().timestamp() - path.stat().st_mtime
    return age < CACHE_TTL_HOURS * 3600


def load_cached_price_data(symbol):
    path = cache_path(symbol)
    if is_cache_valid(path):
        try:
            return pd.read_pickle(path)
        except Exception:
            return None
    return None


def save_cached_price_data(symbol, df):
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        df.to_pickle(cache_path(symbol))
    except Exception:
        pass


def get_next_trading_day(df, signal_date):
    signal_date = pd.to_datetime(signal_date)
    if signal_date not in df.index:
        return None
    position = df.index.get_loc(signal_date)
    next_position = position + 1
    if next_position >= len(df):
        return None
    return df.index[next_position]


def simulate_trade(symbol, signal_date, df, stop_atr=1.0, target_atr=2.0, max_days=10):
    signal_date = pd.to_datetime(signal_date)
    if signal_date not in df.index:
        return None

    next_day = get_next_trading_day(df, signal_date)
    if next_day is None:
        return None

    entry_price = df.loc[next_day, "Open"]
    atr_series = calculate_atr(df)
    entry_atr = atr_series.loc[signal_date]
    if pd.isna(entry_atr) or entry_atr <= 0:
        return None

    stop_loss = entry_price - entry_atr * stop_atr
    take_profit = entry_price + entry_atr * target_atr
    trade_days = df.loc[next_day:next_day + pd.Timedelta(days=max_days * 2)]
    trade_days = trade_days.iloc[:max_days]

    for trade_date, row in trade_days.iterrows():
        low_price = row["Low"]
        high_price = row["High"]
        if low_price <= stop_loss and high_price >= take_profit:
            if row["Close"] >= entry_price:
                return {
                    "symbol": symbol,
                    "signal_date": signal_date.strftime("%Y-%m-%d"),
                    "entry_date": next_day.strftime("%Y-%m-%d"),
                    "exit_date": trade_date.strftime("%Y-%m-%d"),
                    "entry_price": entry_price,
                    "exit_price": take_profit,
                    "result": "win",
                    "reason": "target_hit_same_day",
                    "profit_pct": (take_profit - entry_price) / entry_price * 100,
                    "holding_days": (trade_date - next_day).days,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                }
            return {
                "symbol": symbol,
                "signal_date": signal_date.strftime("%Y-%m-%d"),
                "entry_date": next_day.strftime("%Y-%m-%d"),
                "exit_date": trade_date.strftime("%Y-%m-%d"),
                "entry_price": entry_price,
                "exit_price": stop_loss,
                "result": "loss",
                "reason": "stop_hit_same_day",
                "profit_pct": (stop_loss - entry_price) / entry_price * 100,
                "holding_days": (trade_date - next_day).days,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }
        if high_price >= take_profit:
            return {
                "symbol": symbol,
                "signal_date": signal_date.strftime("%Y-%m-%d"),
                "entry_date": next_day.strftime("%Y-%m-%d"),
                "exit_date": trade_date.strftime("%Y-%m-%d"),
                "entry_price": entry_price,
                "exit_price": take_profit,
                "result": "win",
                "reason": "target_hit",
                "profit_pct": (take_profit - entry_price) / entry_price * 100,
                "holding_days": (trade_date - next_day).days,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }
        if low_price <= stop_loss:
            return {
                "symbol": symbol,
                "signal_date": signal_date.strftime("%Y-%m-%d"),
                "entry_date": next_day.strftime("%Y-%m-%d"),
                "exit_date": trade_date.strftime("%Y-%m-%d"),
                "entry_price": entry_price,
                "exit_price": stop_loss,
                "result": "loss",
                "reason": "stop_hit",
                "profit_pct": (stop_loss - entry_price) / entry_price * 100,
                "holding_days": (trade_date - next_day).days,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
            }

    last_day = trade_days.iloc[-1]
    close_price = last_day["Close"]
    last_date = trade_days.index[-1]
    return {
        "symbol": symbol,
        "signal_date": signal_date.strftime("%Y-%m-%d"),
        "entry_date": next_day.strftime("%Y-%m-%d"),
        "exit_date": last_date.strftime("%Y-%m-%d"),
        "entry_price": entry_price,
        "exit_price": close_price,
        "result": "timeout",
        "reason": "max_days_expired",
        "profit_pct": (close_price - entry_price) / entry_price * 100,
        "holding_days": (last_date - next_day).days,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
    }


def print_simulation_result(result):
    if result is None:
        print("シミュレーションに必要なデータが不足しています。signal_date が価格データに存在するか確認してください。")
        return
    print("\n=== シミュレーション結果 ===")
    print(f"銘柄: {result['symbol']}")
    print(f"シグナル日: {result['signal_date']}")
    print(f"エントリー日: {result['entry_date']}")
    print(f"エントリー価格: {result['entry_price']:.2f}")
    print(f"決済日: {result['exit_date']}")
    print(f"決済価格: {result['exit_price']:.2f}")
    print(f"結果: {result['result'].upper()}")
    print(f"理由: {result['reason']}")
    print(f"損益率: {result['profit_pct']:.2f}%")
    print(f"保有日数: {result['holding_days']}日")
    print(f"損切り価格: {result['stop_loss']:.2f}")
    print(f"利確価格: {result['take_profit']:.2f}")


def write_simulation_result(result):
    if result is None:
        return None
    sim_path = get_available_output_path(
        output_dir / f"simulation_{result['symbol']}_{result['signal_date']}.csv"
    )
    with open(sim_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol","signal_date","entry_date","entry_price","exit_date","exit_price","result","reason","profit_pct","holding_days","stop_loss","take_profit"])
        writer.writerow([
            result["symbol"],
            result["signal_date"],
            result["entry_date"],
            f"{result["entry_price"]:.2f}",
            result["exit_date"],
            f"{result["exit_price"]:.2f}",
            result["result"],
            result["reason"],
            f"{result["profit_pct"]:.2f}",
            result["holding_days"],
            f"{result["stop_loss"]:.2f}",
            f"{result["take_profit"]:.2f}",
        ])
    return sim_path


def parse_args():
    parser = argparse.ArgumentParser(description="候補抽出とトレードシミュレーション")
    parser.add_argument("--simulate-symbol", help="シミュレーション対象の銘柄コード（例: 3964.T）")
    parser.add_argument("--signal-date", help="シグナル日（YYYY-MM-DD）")
    parser.add_argument("--stop-atr", type=float, default=1.0, help="損切りATR倍率（デフォルト 1.0）")
    parser.add_argument("--target-atr", type=float, default=2.0, help="利確ATR倍率（デフォルト 2.0）")
    parser.add_argument("--max-days", type=int, default=10, help="最大保有日数（デフォルト 10日）")
    return parser.parse_args()


def run_simulation(args):
    if not args.simulate_symbol or not args.signal_date:
        print("--simulate-symbol と --signal-date を両方指定してください。")
        return

    price_data = load_price_data([args.simulate_symbol])
    df = price_data.get(args.simulate_symbol)
    if df is None:
        print(f"価格データが見つかりません: {args.simulate_symbol}")
        return

    result = simulate_trade(
        args.simulate_symbol,
        args.signal_date,
        df,
        stop_atr=args.stop_atr,
        target_atr=args.target_atr,
        max_days=args.max_days,
    )
    print_simulation_result(result)
    sim_path = write_simulation_result(result)
    if sim_path:
        print(f"✅ シミュレーション結果を保存しました: {sim_path}")


def get_available_output_path(output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, "a", newline="", encoding="utf-8-sig"):
            pass
        return output_path
    except PermissionError:
        alt_path = output_path.with_name(output_path.stem + "_new" + output_path.suffix)
        print(f"⚠️ 出力ファイルにアクセスできません: {output_path}")
        print(f"   代わりに {alt_path} を使用します。ファイルを閉じて再実行してください。")
        return alt_path


def write_summary_file(output_path, condition_desc, results):
    summary_path = output_path.with_name(output_path.stem + "_summary.txt")
    lines = [
        "=== 初動候補サマリー ===",
        f"出力条件: {condition_desc}",
        "",
        "このファイルは以下の条件で候補を抽出しています。",
        "- 出来高急増（当日出来高 > 直近5日平均出来高）",
        "- 値幅が小さく、初動らしい値動きの銘柄",
        "- 直近5日高値や短期トレンドを重視",
        "- 平均出来高が 50,000 以上の流動性を確保",
        "",
        "戦略メモ:",
        "- 買い: 今日の高値超え、または 5日移動平均付近での押し目買いを検討",
        "- 損切り: 直近安値の少し下、または ATR 1倍下付近",
        "- 利食い: ATR 1.5〜2倍、または直近高値・抵抗線付近",
        "- RSI が高い銘柄は調整リスクがあるため注意",
        "- 出力は候補一覧であり、個別に板・業績・材料を確認すること",
        "",
    ]
    if results:
        lines.append("候補銘柄:")
        for r in results:
            lines.append(
                f"{r['symbol']} {r['name']} score={r['score']} volume_change={r['volume_change']} "
                f"volume_median_ratio={r['volume_median_ratio']} rsi={r['rsi']} price_range={r['price_range']}"
            )
    else:
        lines.append("該当銘柄はありませんでした。条件を緩めて再実行してください。")

    with open(summary_path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines))


def download_price_batch(symbols):
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            raw = yf.download(
                tickers=" ".join(symbols),
                period=FETCH_PERIOD,
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=True,
                group_by="ticker",
            )
        if raw is None or raw.empty:
            return {}

        results = {}
        if isinstance(raw.columns, pd.MultiIndex):
            tickers_in_data = raw.columns.levels[0]
            for symbol in symbols:
                if symbol in tickers_in_data:
                    candidate = raw[symbol].copy()
                    candidate.columns = candidate.columns.get_level_values(0)
                    if not candidate.empty:
                        results[symbol] = candidate
        else:
            if len(symbols) == 1:
                results[symbols[0]] = raw.copy()
        return results
    except Exception:
        return {}


def load_price_data(symbols):
    CACHE_DIR.mkdir(exist_ok=True)
    results = {}
    missing = []

    for symbol in symbols:
        df = load_cached_price_data(symbol)
        if df is not None and not df.empty:
            results[symbol] = df
        else:
            missing.append(symbol)

    for i in range(0, len(missing), BATCH_SIZE):
        batch = missing[i:i + BATCH_SIZE]
        downloaded = download_price_batch(batch)
        for symbol, df in downloaded.items():
            if df is not None and not df.empty:
                save_cached_price_data(symbol, df)
                results[symbol] = df
        for symbol in batch:
            if symbol not in results:
                df = fetch_price_data(symbol)
                if df is not None and not df.empty:
                    save_cached_price_data(symbol, df)
                    results[symbol] = df
    return results


def calculate_score(latest):
    score = 0
    score += 2 if latest["Close"].iloc[0] > latest["prev_high_5"].iloc[0] else 0
    score += 1 if latest["Close"].iloc[0] > latest["sma_short"].iloc[0] else 0
    score += 1 if latest["sma_short"].iloc[0] > latest["sma_long"].iloc[0] else 0
    score += 1 if latest["sma_long"].iloc[0] > latest["sma_mid"].iloc[0] else 0
    score += 1 if latest["rsi"].iloc[0] < 60 else 0
    score += 1 if latest["bb_width"].iloc[0] < 0.06 else 0
    score += 1 if latest["volume_median_ratio"].iloc[0] >= 2 else 0
    score += 1 if latest["avg_volume"].iloc[0] > MIN_VOLUME * 2 else 0
    score -= 1 if latest["rsi"].iloc[0] > 80 else 0
    return score


def detect_initial_move_row(symbol, name, df, vol_threshold, pr_threshold):
    try:
        if df is None or len(df) < max(SMA_MID, BB_PERIOD, ATR_PERIOD) + RSI_PERIOD:
            return None

        df["volume_change"] = df["Volume"] / df["Volume"].rolling(SMA_SHORT).mean()
        df["volume_median"] = df["Volume"].rolling(MEDIAN_VOLUME_PERIOD).median()
        df["volume_median_ratio"] = df["Volume"] / df["volume_median"]
        df["price_range"] = (df["Close"] - df["Open"]).abs() / df["Open"]
        df["avg_volume"] = df["Volume"].rolling(SMA_SHORT).mean()
        df["sma_short"] = df["Close"].rolling(SMA_SHORT).mean()
        df["sma_long"] = df["Close"].rolling(SMA_LONG).mean()
        df["sma_mid"] = df["Close"].rolling(SMA_MID).mean()
        df["rsi"] = calculate_rsi(df["Close"])
        df["atr"] = calculate_atr(df)
        df["bb_mid"] = df["Close"].rolling(BB_PERIOD).mean()
        df["bb_std"] = df["Close"].rolling(BB_PERIOD).std()
        df["bb_upper"] = df["bb_mid"] + 2 * df["bb_std"]
        df["bb_lower"] = df["bb_mid"] - 2 * df["bb_std"]
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]
        df["prev_high_5"] = df["High"].shift(1).rolling(5).max()

        latest = df.iloc[[-1]]
        if pd.isna(latest["avg_volume"].iloc[0]):
            return None

        price_ok = (
            latest["price_range"].iloc[0] >= MIN_PRICE_RANGE and
            latest["price_range"].iloc[0] < pr_threshold
        )
        volume_ok = (
            latest["volume_change"].iloc[0] > vol_threshold and
            latest["avg_volume"].iloc[0] > MIN_VOLUME
        )

        if price_ok and volume_ok:
            score = calculate_score(latest)
            if score < MIN_SCORE:
                return None
            return {
                "symbol": symbol,
                "name": name,
                "date": latest.index[0].strftime("%Y-%m-%d"),
                "open": round(latest["Open"].iloc[0], 2),
                "high": round(latest["High"].iloc[0], 2),
                "low": round(latest["Low"].iloc[0], 2),
                "close": round(latest["Close"].iloc[0], 2),
                "volume_change": round(latest["volume_change"].iloc[0], 2),
                "volume_median_ratio": round(latest["volume_median_ratio"].iloc[0], 2),
                "price_range": round(latest["price_range"].iloc[0], 4),
                "avg_volume": int(latest["avg_volume"].iloc[0]),
                "sma_short": round(latest["sma_short"].iloc[0], 2),
                "sma_long": round(latest["sma_long"].iloc[0], 2),
                "sma_mid": round(latest["sma_mid"].iloc[0], 2),
                "rsi": round(latest["rsi"].iloc[0], 1),
                "atr": round(latest["atr"].iloc[0], 2),
                "bb_width": round(latest["bb_width"].iloc[0], 3),
                "prev_high_5": round(latest["prev_high_5"].iloc[0], 2),
                "score": score,
            }
    except Exception:
        return None
    return None

# --- ステップ③：全銘柄ループ処理 ---
def main(args=None):
    if args is None:
        args = parse_args()

    if args.simulate_symbol or args.signal_date:
        if not args.simulate_symbol or not args.signal_date:
            print("--simulate-symbol と --signal-date を両方指定してください。")
            return
        run_simulation(args)
        return

    start = time.time()
    symbols_df = load_prime_symbols_from_xls(DATA_XLS_PATH)
    total = len(symbols_df)
    print(f"📥 全銘柄数: {total}件")
    price_data = load_price_data(symbols_df["code"].tolist())
    print(f"📦 価格データ取得済み: {len(price_data)} / {total} 件")

    for idx, condition in enumerate(CONDITIONS, 1):
        vol_th = condition["volume_change"]
        pr_th = condition["price_range"]
        condition_desc = f"volume_change > {vol_th}, price_range < {pr_th}, MIN_VOLUME > {MIN_VOLUME}"

        print(f"\n🔍 条件セット {idx}: volume_change > {vol_th}, price_range < {pr_th}")

        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for row in symbols_df.itertuples():
                df = price_data.get(row.code)
                if df is None:
                    continue
                futures.append(executor.submit(detect_initial_move_row, row.code, row.symbol, df, vol_th, pr_th))
            for i, future in enumerate(as_completed(futures), 1):
                if i % 100 == 0:
                    print(f"🚀 {i}件処理中...")
                result = future.result()
                if result:
                    result["condition"] = idx
                    result["condition_desc"] = condition_desc
                    results.append(result)

        filtered_results = [r for r in results if r["score"] >= MIN_SCORE]
        if filtered_results:
            output_path = get_available_output_path(output_dir / f"initial_move_candidates_v{idx}_{today_str}.csv")
            with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([f"# 条件: {condition_desc}"])
                results_df = pd.DataFrame(filtered_results).sort_values("score", ascending=False).reset_index(drop=True)
                writer.writerow(results_df.columns)
                writer.writerows(results_df.values)
            write_summary_file(output_path, condition_desc, filtered_results)
            print(f"\n✅ 条件セット {idx} にて {len(filtered_results)}件検出 → {output_path}")
            print(f"✅ サマリーファイル出力 → {output_path.with_name(output_path.stem + '_summary.txt')}")
            return

        if results:
            print(f"⛔ 条件セット {idx} は候補がありませんでした（{condition_desc}、score >= {MIN_SCORE}）")
        else:
            print(f"⛔ 条件セット {idx} は該当なし（{condition_desc}）")

    print("\n⚠️ どの条件セットでも候補が見つかりませんでした。別条件で再実行してください。")
    return


if __name__ == "__main__":
    main()
