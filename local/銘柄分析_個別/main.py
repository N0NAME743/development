# ==============================
# main.py｜Gyazoアップロード + JSONログ + CSV出力 + Slack通知 + 進捗表示
# ==============================

import os
import json
import csv
import time
import hashlib
import argparse
from datetime import datetime
import matplotlib.pyplot as plt

from setup import JP_FONT
from stock_data import get_symbols_from_excel, fetch_stock_data
from chart_config import add_indicators, plot_chart
from gyazo_uploader import upload_to_gyazo
from slack_notifier import send_to_slack  # ✅ Slack通知用

# ==============================
# 設定
# ==============================

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL") or "https://hooks.slack.com/services/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"

# 🎯 コマンドライン引数に --upload, --slack を追加
parser = argparse.ArgumentParser(description="株価チャート自動処理")
parser.add_argument("--upload", action="store_true", help="Gyazoにアップロードする")
parser.add_argument("--slack", action="store_true", help="Slack通知を有効にする")
args = parser.parse_args()
ENABLE_GYAZO_UPLOAD = args.upload
ENABLE_SLACK = args.slack
GYAZO_ACCESS_TOKEN = "VbP8FQFvnNREgTPDnSSNTgNaOfVwS2DZOCZDmPMclYU"
plt.rcParams['font.family'] = JP_FONT

# ==============================
# 日付ベースの保存パス
# ==============================

today_str = datetime.today().strftime('%Y-%m-%d')
LOG_PATH_ALL = "result/gyazo_log.json"
LOG_PATH_DAILY = f"result/{today_str}/gyazo_log.json"
os.makedirs(os.path.dirname(LOG_PATH_ALL), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH_DAILY), exist_ok=True)

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

# ==============================
# メイン処理
# ==============================

def main():
    symbols = get_symbols_from_excel()
    total = len(symbols)
    uploaded_hashes, log_data_all = load_uploaded_hashes_json(LOG_PATH_ALL)
    _, log_data_daily = load_uploaded_hashes_json(LOG_PATH_DAILY)
    uploaded_today = []

    if total == 0:
        print("❌ 処理対象の銘柄がありません")
        return

    print(f"✅ Excelから読み込み成功: {total}銘柄")
    print("━━━━━━━━━━━━━━━━━━━━")

    start_time = time.time()

    for idx, symbol in enumerate(symbols, 1):
        t0 = time.time()
        print(f"▶ 処理中: {symbol} │ {idx}/{total}件中", end="")

        try:
            df, name = fetch_stock_data(symbol)
            if df is None:
                raise ValueError("データ取得失敗")

            df = add_indicators(df)
            image_path, signals, signal_comment = plot_chart(df, symbol, name)
            image_hash = get_file_md5(image_path)

            # ✅ アップロード済みの場合 → Slack通知だけ送る
            if image_hash in uploaded_hashes:
                print(" ⏭ すでにアップロード済み")

                # Slack通知は新規アップロード時だけにしたいのでここは無効化
                if ENABLE_SLACK:
                    print(f"🚫 Slack通知スキップ（すでにアップロード済み: {symbol}）")
                    #matched = next((entry for entry in log_data_all if entry["hash"] == image_hash), None)
                    #if matched:
                    #    msg = f"*📈 {matched['name']} ({matched['symbol']})*\n{matched['comment']}\n📸 {matched['gyazo_url'] or '画像なし'}"
                    #    time.sleep(1)  # ← Slackは1秒間隔で安全
                    #  send_to_slack(SLACK_WEBHOOK_URL, msg)

                continue

            # ✅ 新規アップロード処理
            gyazo_url = None
            if ENABLE_GYAZO_UPLOAD:
                desc = f"{symbol} {name} の株価チャート（{today_str}）"
                time.sleep(1)  # ← Gyazo側のレートリミット回避
                gyazo_url = upload_to_gyazo(image_path, GYAZO_ACCESS_TOKEN, desc=desc)

            new_entry = {
                "symbol": symbol,
                "name": name,
                "date": today_str,
                "image_path": image_path,
                "gyazo_url": gyazo_url,
                "hash": image_hash,
                "score": None,
                "comment": signal_comment,
                "signals": signals
            }

            append_upload_log_json(LOG_PATH_ALL, log_data_all, new_entry)
            append_upload_log_json(LOG_PATH_DAILY, log_data_daily, new_entry)
            uploaded_today.append(new_entry)

            # ✅ Slack通知（新規アップロード時も送信）
            if ENABLE_SLACK:
                msg = f"*📈 {name} ({symbol})*\n{signal_comment}\n📸 {gyazo_url or '画像なし'}"
                time.sleep(1)  # ← Slackは1秒間隔で安全
                send_to_slack(SLACK_WEBHOOK_URL, msg)
            else:
                print("🚫 Slack通知スキップ（--slack未指定）")

            elapsed = time.time() - t0
            remaining = elapsed * (total - idx)
            mins, secs = divmod(int(remaining), 60)

            if ENABLE_GYAZO_UPLOAD:
                print(f" ✅ Gyazo: {gyazo_url or '❌'} │ 残り: {mins}分{secs}秒")
            else:
                print(f" 🚫 Gyazoスキップ │ 残り: {mins}分{secs}秒")

        except Exception as e:
            print(f"\n❌ エラー発生: {symbol} - {e}")

    total_time = time.time() - start_time
    t_min, t_sec = divmod(int(total_time), 60)

    out_folder = f"result/{today_str}"
    os.makedirs(out_folder, exist_ok=True)
    write_gyazo_csv(out_folder, uploaded_today)

    print("━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 全銘柄処理完了（所要時間: {t_min}分{t_sec}秒）")
    print(f"📄 CSV出力: {out_folder}/gyazo_uploaded.csv")

if __name__ == "__main__":
    main()
