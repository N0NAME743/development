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
from slack_notifier import send_signal_summary
from database import load_latest_data, init_db, save_price_data  # ✅ SQLite対応
from analyzer import analyze_stock, classify_signals

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

def detect_signals(df_all):
    buy_signals = []
    sell_signals = []

    for symbol in df_all["symbol"].unique():
        df_symbol = df_all[df_all["symbol"] == symbol].copy()
        if df_symbol.empty or len(df_symbol) < 30:
            continue
        df_symbol = df_symbol.sort_values("date")  # 念のため時系列に並び替え

        # 🧠 統合分析ロジックを使用
        signals, _, _, attention, _, _ = analyze_stock(df_symbol)

        name = df_symbol["name"].iloc[-1]

        # 🎯 通知条件：attention の文字列を使う
        if "買" in attention:
            buy_signals.append(f"{symbol}（{name}）: {attention} | {', '.join(signals)}")
        elif "売" in attention:
            sell_signals.append(f"{symbol}（{name}）: {attention} | {', '.join(signals)}")

    return buy_signals, sell_signals

def notify_signal_alerts():
    df = load_latest_data()
    df = df.drop_duplicates("symbol", keep="last")  # ← ★これで重複防止！
    buy_list, sell_list = detect_signals(df)
    send_signal_summary("📈 買いシグナル銘柄", buy_list)
    send_signal_summary("📉 売りシグナル銘柄", sell_list)

def notify_signal_alerts_from_uploaded(uploaded_today):
    buy_list, sell_list, neutral_list = [], [], []

    for entry in uploaded_today:
        attention = entry.get("attention", "")
        symbol = entry["symbol"]
        name = entry["name"]
        signals = entry["signals"]

        buy_signals = signals.get("buy", [])
        sell_signals = signals.get("sell", [])

        total_signals = len(buy_signals) + len(sell_signals)

        # ✅ 買い優勢（買いシグナル3個以上）
        if len(buy_signals) >= 3:
            summary = f"{symbol}（{name}）: {attention} | " + "、".join(buy_signals)
            buy_list.append(summary)

        # ✅ 売り優勢（売りシグナル3個以上）
        elif len(sell_signals) >= 3:
            summary = f"{symbol}（{name}）: {attention} | " + "、".join(sell_signals)
            sell_list.append(summary)

        # ✅ シグナル総数が多いが、判断が難しい場合（様子見扱い）
        elif total_signals >= 4:
            summary = f"{symbol}（{name}）: {attention} | "
            parts = []
            if buy_signals:
                parts.append("📈 " + "、".join(buy_signals))
            if sell_signals:
                parts.append("📉 " + "、".join(sell_signals))
            summary += " / ".join(parts)
            neutral_list.append(summary)

    # ✅ 通知実行
    send_signal_summary("📈 買いシグナル銘柄", buy_list)
    send_signal_summary("📉 売りシグナル銘柄", sell_list)
    send_signal_summary("🌀 シグナル混在（様子見）", neutral_list)

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
                print("⏭ すでにアップロード済み")
                if ENABLE_SLACK:
                    print(f"🚫 Slack通知スキップ（すでにアップロード済み: {symbol}）")
                else:
                    print("🚫 Slack通知スキップ（--slack未指定）")
                print("🚫 Gyazoスキップ（--upload未指定）")
                print("🗃️ DB登録: スキップ（アップロード済）")

                continue  # ← ログだけ出したあとにスキップ

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
                "attention": attention,
                "comment": comment,
                "signals": signal_dict  # ← 分類された形で保存！
            }
            append_upload_log_json(LOG_PATH_ALL, log_data_all, new_entry)
            append_upload_log_json(LOG_PATH_DAILY, log_data_daily, new_entry)
            uploaded_today.append(new_entry)

            # ✅ Slack通知（新規のみ）
            if ENABLE_SLACK:
                signal_lines = []
                if signals.get("buy"):
                    signal_lines.append(f"📈 買い: {', '.join(signals['buy'])}")
                if signals.get("sell"):
                    signal_lines.append(f"📉 売り: {', '.join(signals['sell'])}")
                if signals.get("neutral"):
                    signal_lines.append(f"⚪ 中立: {', '.join(signals['neutral'])}")
                
                signal_summary = "\n".join(signal_lines)

                msg = f"*{name} ({symbol})*\n{comment}\n{signal_summary}\n📸 {gyazo_url or '画像なし'}"
                time.sleep(1)
                send_to_slack(SLACK_WEBHOOK_URL, msg)
            else:
                print("🚫 Slack通知スキップ（--slack未指定）")

            # ✅ 進捗表示
            elapsed = time.time() - t0
            remaining = elapsed * (total - idx)
            mins, secs = divmod(int(remaining), 60)

            # ▶ 進捗ヘッダー
            print(f"\n▶ 処理中: {symbol} │ {idx}/{total}件中／残り: {mins}分{secs}秒")
            # 📈 チャート出力ログ（重複除去）
            print(f"📈 チャート画像: {image_path}")
            # 🚫 Slack通知
            if ENABLE_SLACK:
                print("✅ Slack通知送信済み")
            else:
                print("🚫 Slack通知スキップ（--slack未指定）")
            # 🚫 Gyazo通知
            if ENABLE_GYAZO_UPLOAD:
                print(f"✅ Gyazoアップロード: {gyazo_url or '❌'}")
            else:
                print("🚫 Gyazoスキップ（--upload未指定）")
            # 🗃️ DB登録ログ（仮に件数を決め打ちしていたらそのまま）
            count = save_price_data(df, symbol, name)
            print(f"🗃️ DB登録: {count}件 ({symbol})")

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