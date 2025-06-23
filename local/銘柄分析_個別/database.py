import sqlite3
from pathlib import Path
import os

DB_PATH = Path("result/stock_data.db")

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
            senkou2 REAL
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
        "ADX", "STOCH_K", "senkou1", "senkou2"
    }]
    df = df[cols]

    # ✅ 列名をすべて小文字に統一
    df.columns = [c.lower() for c in df.columns]

    # ✅ 重複行を除去（同一銘柄・同一日）
    df = df.drop_duplicates(subset=["symbol", "date"])

    # ✅ SQLiteに追記
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("price_history", conn, if_exists="append", index=False)

    print(f"|{len(df)}件DBに登録 ({symbol})")

