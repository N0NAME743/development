# ==============================
# main.py｜チャート処理・データ保存・通知（Gyazo / Slack / DB対応）
# ==============================

# 標準ライブラリ
import os
import json
import csv
import time
import hashlib
import argparse
from datetime import datetime

# サードパーティライブラリ
import matplotlib.pyplot as plt
from dotenv import load_dotenv  # ✅ .envから環境変数を読み込み

# 自作モジュール（プロジェクト内）
from setup import JP_FONT
from stock_data import get_symbols_from_excel, fetch_stock_data
from chart_config import add_indicators, plot_chart
from gyazo_uploader import upload_to_gyazo
from slack_notifier import send_to_slack
from database import init_db, save_price_data  # ✅ SQLite対応

# ==============================
# 初期設定
# ==============================

# ✅ フォント設定（matplotlib用）
plt.rcParams["font.family"] = JP_FONT

# ✅ 環境変数を読み込む（.envファイル）
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
GYAZO_ACCESS_TOKEN = os.getenv("GYAZO_ACCESS_TOKEN")

# ✅ SQLite データベース初期化
init_db()

# ==============================
# 引数設定（コマンドライン用）
# ==============================

parser = argparse.ArgumentParser(description="株価チャート自動処理")
parser.add_argument("--upload", action="store_true", help="Gyazoアップロードを有効にする")
parser.add_argument("--slack", action="store_true", help="Slack通知を有効にする")
args = parser.parse_args()
ENABLE_GYAZO_UPLOAD = args.upload
ENABLE_SLACK = args.slack

# ==============================
# 日付ベースの保存パス
# ==============================

today_str = datetime.today().strftime('%Y-%m-%d')      # 既存の日付（例：2025-06-23）
today_compact = datetime.today().strftime('%Y%m%d')    # 新しい形式（例：20250623）

#LOG_PATH_ALL = "result/gyazo_log.json"
LOG_PATH_ALL = f"result/signal_log_{datetime.today().year}.json" # 年ごとにログを分ける
LOG_PATH_DAILY = f"result/{today_str}/signal_log_{today_compact}.json"
os.makedirs(os.path.dirname(LOG_PATH_ALL), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH_DAILY), exist_ok=True)

csv_filename = f"signal_chart_uploaded_{today_compact}.csv"  # today_str = 2025-06-23

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

def write_gyazo_csv(csv_path, entries):
    file_exists = os.path.exists(csv_path)
    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
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
            if df is None or df.empty:
                raise ValueError("データ取得失敗 or 空データ")

            print(f"▶ {symbol} の取得後カラム: {df.columns.tolist()}")

            df = add_indicators(df)
            save_price_data(df, symbol, name) # ✅ SQLiteへの保存   

            image_path, signals, signal_comment = plot_chart(df, symbol, name)
            image_hash = get_file_md5(image_path)

            # ✅ アップロード済みの場合はスキップ
            if image_hash in uploaded_hashes:
                print(" ⏭ すでにアップロード済み")
                if ENABLE_SLACK:
                    print(f"🚫 Slack通知スキップ（すでにアップロード済み: {symbol}）")
                continue

            # ✅ 新規アップロード
            gyazo_url = None
            if ENABLE_GYAZO_UPLOAD:
                desc = f"{symbol} {name} の株価チャート（{today_str}）"
                time.sleep(1)
                gyazo_url = upload_to_gyazo(image_path, GYAZO_ACCESS_TOKEN, desc=desc)

            # ✅ ログ追記
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

            # ✅ Slack通知（新規のみ）
            if ENABLE_SLACK:
                msg = f"*📈 {name} ({symbol})*\n{signal_comment}\n📸 {gyazo_url or '画像なし'}"
                time.sleep(1)
                send_to_slack(SLACK_WEBHOOK_URL, msg)
            else:
                print("🚫 Slack通知スキップ（--slack未指定）")

            # ✅ 進捗表示
            elapsed = time.time() - t0
            remaining = elapsed * (total - idx)
            mins, secs = divmod(int(remaining), 60)

            if ENABLE_GYAZO_UPLOAD:
                print(f" ✅ Gyazo: {gyazo_url or '❌'} │ 残り: {mins}分{secs}秒")
            else:
                print(f" 🚫 Gyazoスキップ │ 残り: {mins}分{secs}秒")

        except Exception as e:
            print(f"\n❌ エラー発生: {symbol} - {e}")

    print("✅ 全銘柄処理完了（所要時間: {:.1f}秒）".format(time.time() - start_time))
    return uploaded_today

if __name__ == "__main__":
    uploaded_today = main()
    # オプション：アップロードした分をCSVにも保存
    if uploaded_today:
        write_gyazo_csv(os.path.join("result", csv_filename), uploaded_today)
