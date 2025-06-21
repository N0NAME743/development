# ==============================
# main.py｜Gyazoアップロード + JSONログ + CSV出力（統合版）
# ==============================

import os
import json
import csv
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt

from setup import JP_FONT
from stock_data import get_symbols_from_excel, fetch_stock_data
from chart_config import add_indicators, plot_chart
from gyazo_uploader import upload_to_gyazo

# ✅ フォント設定
plt.rcParams['font.family'] = JP_FONT

# ✅ Gyazoアップロードを有効にするか
ENABLE_GYAZO_UPLOAD = False  # ← False にするとアップロード処理をスキップ

# ==============================
# 補助関数群
# ==============================

def load_uploaded_hashes_json(log_path):
    if not os.path.exists(log_path):
        return set(), []
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return set(entry["hash"] for entry in data), data

def append_upload_log_json(log_path, log_data, new_entry):
    log_data.append(new_entry)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def write_gyazo_csv(out_folder, entries):
    out_path = os.path.join(out_folder, "gyazo_uploaded.csv")
    file_exists = os.path.exists(out_path)
    with open(out_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "symbol", "name", "hash", "url"])
        if not file_exists:
            writer.writeheader()
        for entry in entries:
            writer.writerow({
                "date": entry["date"],
                "symbol": entry["symbol"],
                "name": entry["name"],
                "hash": entry["hash"],
                "url": entry.get("gyazo_url", "")
            })

# ✅ 各種パスと設定

today_str = datetime.today().strftime('%Y-%m-%d')
LOG_PATH_ALL = "result/gyazo_log.json"
LOG_PATH_DAILY = f"result/{today_str}/gyazo_log.json"

# ✅ Gyazoトークン（必要に応じて変更）
GYAZO_ACCESS_TOKEN = "YOUR_GYAZO_ACCESS_TOKEN_HERE"

# フォルダ作成
os.makedirs(os.path.dirname(LOG_PATH_ALL), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH_DAILY), exist_ok=True)

# ==============================
# メイン処理
# ==============================

def main():
    symbols = get_symbols_from_excel()
    uploaded_hashes, log_data_all = load_uploaded_hashes_json(LOG_PATH_ALL)
    _, log_data_daily = load_uploaded_hashes_json(LOG_PATH_DAILY)
    uploaded_today = []

    print(f"✅ Excelから読み込み成功: {len(symbols)}銘柄")

    for symbol in symbols:
        print(f"▶ 処理中: {symbol}")
        df, name = fetch_stock_data(symbol)
        if df is None:
            print(f"⚠ データ取得スキップ: {symbol}")
            continue

        df = add_indicators(df)
        image_path = plot_chart(df, symbol, name)
        image_hash = get_file_md5(image_path)

        if image_hash in uploaded_hashes:
            print(f"⏭ すでにアップロード済み（同一内容）: {image_path}")
            continue

        desc = f"{symbol} {name} の株価チャート（{today_str}）"
        gyazo_url = None

        if ENABLE_GYAZO_UPLOAD:
            gyazo_url = upload_to_gyazo(image_path, GYAZO_ACCESS_TOKEN, desc=desc)

        new_entry = {
            "symbol": symbol,
            "name": name,
            "date": today_str,
            "image_path": image_path,
            "gyazo_url": gyazo_url,
            "hash": image_hash,
            "score": None,
            "comment": None
        }

        append_upload_log_json(LOG_PATH_ALL, log_data_all, new_entry)
        append_upload_log_json(LOG_PATH_DAILY, log_data_daily, new_entry)
        uploaded_today.append(new_entry)

        if ENABLE_GYAZO_UPLOAD and gyazo_url:
            print(f"\U0001F517 Gyazo URL 保存: {gyazo_url}")
        elif ENABLE_GYAZO_UPLOAD:
            print("⚠ Gyazoアップロードに失敗しました")
        else:
            print("🚫 Gyazoアップロードはスキップされました")

    out_folder = f"result/{today_str}"
    os.makedirs(out_folder, exist_ok=True)
    write_gyazo_csv(out_folder, uploaded_today)
    print(f"✅ Gyazoアップロード履歴CSVを書き出しました: {out_folder}/gyazo_uploaded.csv")

if __name__ == "__main__":
    main()
