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
import pandas as pd
from dotenv import load_dotenv  # ✅ .envから環境変数を読み込み

# 自作モジュール（プロジェクト内）
from setup import JP_FONT
from stock_data import get_symbols_from_excel, fetch_stock_data
from chart_config import add_indicators, plot_chart
from gyazo_uploader import GyazoUploader
from slack_notifier import notify_signal_alerts_from_uploaded  # ✅ Slack通知
from database import load_latest_data, init_db, save_price_data  # ✅ SQLite対応
from analyzer import analyze_stock, classify_signals, detect_signals  # ✅ 分析・シグナル検出

# ==============================
# 初期設定
# ==============================

# ✅ フォント設定（matplotlib用）
plt.rcParams["font.family"] = JP_FONT

# ✅ 環境変数を読み込む（.envファイル）
load_dotenv()
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
    """
    同一の symbol, date, name を持つエントリが存在する場合は、古いものを削除して新しいエントリを追加。
    """
    # 一意な識別キー（symbol + date + name）で重複判定
    unique_key = (new_entry["symbol"], new_entry["date"], new_entry["name"])
    # 重複エントリを削除（破壊的変更）
    log_data[:] = [
        e for e in log_data
        if (e.get("symbol"), e.get("date"), e.get("name")) != unique_key
    ]
    # 更新日時も記録（任意）
    from datetime import datetime
    new_entry["updated_at"] = datetime.now().isoformat(timespec="seconds")
    # 新しいエントリを追加
    log_data.append(new_entry)
    # JSONファイルに書き込み
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
    uploader = GyazoUploader()  # ← 追加！
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

        try:
            df, name = fetch_stock_data(symbol)
            if df is None or df.empty:
                raise ValueError("データ取得失敗 or 空データ")

            df = add_indicators(df)
            #save_price_data(df, symbol, name) # ✅ SQLiteへの保存   

            # 1銘柄ずつ処理するループ内（例: for symbol in symbols ...）
            signals, comment, _, attention, _, _ = analyze_stock(df)
            signal_dict = classify_signals(signals)  # ← 分類する！

            # ✅ チャート出力（必要に応じて comment を渡す設計に変更）
            image_path, signals, signal_comment = plot_chart(df, symbol, name)
            image_hash = get_file_md5(image_path)

            # ✅ アップロード済みの場合はスキップ
            if image_hash in uploaded_hashes:
                elapsed = time.time() - t0
                remaining = elapsed * (total - idx)
                mins, secs = divmod(int(remaining), 60)

                print(f"\n▶ 処理中: {symbol} │ {idx}/{total}件中／残り: {mins}分{secs}秒")
                print(f"📈 チャート画像: {image_path}")

                # Gyazoアップロードスキップ理由を明示
                if ENABLE_GYAZO_UPLOAD:
                    print("⏭ Gyazoアップロード：スキップ（すでにアップロード済み）")
                else:
                    print("🚫 Gyazoスキップ（--upload未指定）")

                # DB登録スキップ理由
                print("🗃️ DB登録: スキップ（アップロード済）")

                continue  # スキップして次の銘柄へ

            # ✅ 新規アップロード（堅牢版）
            gyazo_url = None
            if ENABLE_GYAZO_UPLOAD:
                desc = f"{symbol} {name} の株価チャート（{today_str}）"
                gyazo_url = uploader.upload(image_path, desc=desc)

            # ✅ ログ追記
            new_entry = {
                "symbol": symbol,
                "name": name,
                "date": today_str,
                "updated_at":datetime.now().isoformat(timespec="seconds"),
                "image_path": image_path,
                "gyazo_url": gyazo_url,
                "hash": image_hash,
                "attention": attention,
                "comment": comment,
                "signals": signal_dict  # ← 分類された形で保存！
            }
            append_upload_log_json(LOG_PATH_ALL, log_data_all, new_entry)
            append_upload_log_json(LOG_PATH_DAILY, log_data_daily, new_entry)
            uploaded_today.append(new_entry)

            # ✅ 進捗表示
            elapsed = time.time() - t0
            remaining = elapsed * (total - idx)
            mins, secs = divmod(int(remaining), 60)

            # ▶ 進捗ヘッダー
            print(f"\n▶ 処理中: {symbol} │ {idx}/{total}件中／残り: {mins}分{secs}秒")
            # 📈 チャート出力ログ（重複除去）
            print(f"📈 チャート画像: {image_path}")
            # 🚫 Gyazo通知
            if ENABLE_GYAZO_UPLOAD:
                print(f"✅ Gyazoアップロード: {gyazo_url or '❌'}")
            else:
                print("🚫 Gyazoスキップ（--upload未指定）")
            # 🗃️ DB登録ログ（仮に件数を決め打ちしていたらそのまま）
            result = save_price_data(df, symbol, name)
            if result["status"] == "inserted":
                print(f"🗃️ DB登録: {result['count']}件 ({symbol})")
            else:
                print(f"🗃️ DB登録スキップ: ({symbol})（すでに登録済）")

        except Exception as e:
            print(f"\n❌ エラー発生: {symbol} - {e}")

    print("✅ 全銘柄処理完了（所要時間: {:.1f}秒）".format(time.time() - start_time))
    return uploaded_today

if __name__ == "__main__":
    uploaded_today = main()
    # オプション：アップロードした分をCSVにも保存
    if uploaded_today:
        daily_folder = os.path.join("result", today_str)  # 例: result/2025-06-23/
        csv_path = os.path.join(daily_folder, csv_filename)
        write_gyazo_csv(csv_path, uploaded_today)

    #notify_signal_alerts()  # ✅ Slack通知を実行
    notify_signal_alerts_from_uploaded(uploaded_today)

    # === JSON → CSV出力部分（uploaded_today関係なく常に実行） ===
    daily_folder = os.path.join("result", today_str)
    os.makedirs(daily_folder, exist_ok=True)

    # 🔧 事前初期化（エラー回避用）
    buy_csv_path = ""
    sell_csv_path = ""
    buy_entries = []
    sell_entries = []

    log_json_path = os.path.join(daily_folder, f"signal_log_{today_compact}.json")

    # ✅ JSONがあれば読み込み、なければ uploaded_today から作成
    if os.path.exists(log_json_path):
        with open(log_json_path, "r", encoding="utf-8") as f:
            all_entries = json.load(f)
        print(f"📥 既存のJSONログを読み込み: {log_json_path}")

        # ✅ 重複除去（symbol＋date）
        unique_entries = {}
        for e in all_entries:
            key = (e["symbol"], e["date"])
            if key not in unique_entries:
                unique_entries[key] = e
        all_entries = list(unique_entries.values())

    elif uploaded_today:
        with open(log_json_path, "w", encoding="utf-8") as f:
            json.dump(uploaded_today, f, ensure_ascii=False, indent=2)
        all_entries = uploaded_today
        print(f"🆕 JSONログを新規作成: {log_json_path}")
    else:
        print("⚠️ JSONログが存在せず、uploaded_today も空のため、出力をスキップします。")
        all_entries = []

    # ✅ CSV出力処理
    if all_entries:
        def format_csv_rows(entries):
            return [ {
                "symbol": e["symbol"],
                "name": e["name"],
                "date": e["date"],
                "attention": e["attention"],
                "comment": e["comment"],
                "signals_buy": "、".join(e["signals"].get("buy", [])),
                "signals_sell": "、".join(e["signals"].get("sell", [])),
                "gyazo_url": e.get("gyazo_url", ""),
                "image_path": e.get("image_path", "")
            } for e in entries ]

        buy_entries = [e for e in all_entries if "買い" in e.get("attention", "")]
        sell_entries = [e for e in all_entries if "売り" in e.get("attention", "")]

        buy_csv_path = os.path.join(daily_folder, f"signal_filtered_buy_{today_compact}.csv")
        sell_csv_path = os.path.join(daily_folder, f"signal_filtered_sell_{today_compact}.csv")

        pd.DataFrame(format_csv_rows(buy_entries)).to_csv(buy_csv_path, index=False)
        pd.DataFrame(format_csv_rows(sell_entries)).to_csv(sell_csv_path, index=False)

        print(f"📤 買い銘柄CSV出力: {buy_csv_path}")
        print(f"📤 売り銘柄CSV出力: {sell_csv_path}")
    else:
        print("⚠️ 出力対象のデータが空です。CSV出力はスキップされました。")

    # ✅ Slack通知（ファイル添付付き：Bot連携）
    from slack_notifier import send_summary_with_files

    if ENABLE_SLACK and (buy_entries or sell_entries):
        send_summary_with_files(
            buy_csv_path=buy_csv_path,
            sell_csv_path=sell_csv_path,
            buy_count=len(buy_entries),
            sell_count=len(sell_entries),
            date_str=today_str
        )
    else:
        print("🚫 Slack通知（添付付き）スキップ：--slack未指定 or データなし")

