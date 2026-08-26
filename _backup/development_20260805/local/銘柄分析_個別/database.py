# ==============================
# Sec｜database.py
# ==============================

import sqlite3
import pandas as pd
from pathlib import Path
import os

DB_PATH = Path("result/stock_data.db")

def load_latest_data():
    with sqlite3.connect(DB_PATH) as conn:
        latest_date = pd.read_sql_query("SELECT MAX(date) as max_date FROM price_history", conn)["max_date"][0]
        df = pd.read_sql_query(f"SELECT * FROM price_history WHERE date = '{latest_date}'", conn)
    return df

def init_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # ✅ テーブル作成
        conn.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            date TEXT,
            symbol TEXT,
            name TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            ma5 REAL,
            ma25 REAL,
            ma75 REAL,
            rsi REAL,
            macd REAL,
            macd_signal REAL,
            macd_diff REAL,
            adx REAL,
            stoch_k REAL,
            senkou1 REAL,
            senkou2 REAL,
            bb_upper REAL,     -- ✅ 追加
            bb_middle REAL,    -- ✅ 中央線（＝移動平均）
            bb_lower REAL,     -- ✅ 追加
            kairi_25 REAL,     -- ✅ 25日乖離率を追加
            atr REAL           -- ✅ ATRを追加
        )
        """)
        # ✅ インデックス作成
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_symbol_date 
        ON price_history(symbol, date)
        """)

def save_price_data(df, symbol, name):
    df = df.copy()
    df["symbol"] = symbol
    df["name"] = name
    df["date"] = df.index.strftime("%Y-%m-%d")
    df = df.reset_index()

    # ✅ 必要な列のみ抽出
    cols = [c for c in df.columns if c in {
        "date", "symbol", "name", "Open", "High", "Low", "Close", "Volume",
        "MA5", "MA25", "MA75", "RSI", "MACD", "MACD_signal", "MACD_diff",
        "ADX", "STOCH_K", "senkou1", "senkou2",
        "BB_upper", "BB_middle", "BB_lower",
        "KAIRI_25", "ATR"
    }]
    df = df[cols]
    df.columns = [c.lower() for c in df.columns]
    df = df.drop_duplicates(subset=["symbol", "date"])

    # ✅ 保存前に現在DBにあるデータを読み込んで差分をとる
    import sqlite3
    from pathlib import Path

    DB_PATH = Path("result/stock_data.db")

    with sqlite3.connect(DB_PATH) as conn:
        # 現在のDBに存在するsymbol+dateの組み合わせを取得
        existing = pd.read_sql_query("""
            SELECT symbol, date FROM price_history WHERE symbol = ?;
        """, conn, params=(symbol,))
        existing_keys = set(zip(existing["symbol"], existing["date"]))

        # 新規のみ抽出
        df_new = df[~df.apply(lambda row: (row["symbol"], row["date"]) in existing_keys, axis=1)]

        # 登録
        if not df_new.empty:
            df_new.to_sql("price_history", conn, if_exists="append", index=False)

    return {
        "status": "inserted" if len(df_new) > 0 else "skipped",
        "count": len(df_new)
    }
