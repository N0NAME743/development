import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_signal_summary(title: str, signals: list):
    """
    Slackに注目銘柄のシグナル一覧を送信する。
    """
    if not SLACK_WEBHOOK_URL or not SLACK_WEBHOOK_URL.startswith("https://hooks.slack.com/"):
        print(f"🚫 Slack Webhook URLが設定されていないか不正です（.envを確認）")
        return
    if not signals:
        print(f"🚫 通知対象なし: {title}")
        return

    message = f"*{title}*\n" + "\n".join(f"- {item}" for item in signals)
    payload = {"text": message}

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print(f"✅ Slack送信成功: {title}")
        else:
            print(f"❌ Slack通知失敗: {response.status_code} - {response.text}")
            backup_failed_message(title, signals)
    except Exception as e:
        print(f"❌ Slack通知中にエラー発生: {e}")
        backup_failed_message(title, signals)

def backup_failed_message(title, signals):
    dt = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("result", exist_ok=True)
    path = f"result/failed_slack_{dt}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"title": title, "signals": signals}, f, ensure_ascii=False, indent=2)
    print(f"📝 送信失敗メッセージを保存: {path}")

def send_to_slack(url, text):
    payload = {"text": text}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Slack通知送信成功")
        else:
            print(f"❌ Slack通知失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Slack通知中にエラー発生: {e}")

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

        # Slack整形用関数
        def format_entry(symbol, name, attention, label, signals):
            return f"*{symbol}（{name}）: {attention}*\n💡指標 │ {label}：{ '、'.join(signals) }"

        # ✅ 買い優勢（買いシグナル3個以上）
        if len(buy_signals) >= 3:
            summary = format_entry(symbol, name, attention, "買い", buy_signals)
            buy_list.append(summary)

        # ✅ 売り優勢（売りシグナル3個以上）
        elif len(sell_signals) >= 3:
            summary = format_entry(symbol, name, attention, "売り", sell_signals)
            sell_list.append(summary)

        # ✅ シグナル混在（様子見）
        elif total_signals >= 4:
            summary = f"{symbol}（{name}）: *{attention}*\n"
            if buy_signals:
                summary += f"📈 買い：{ '、'.join(buy_signals) }\n"
            if sell_signals:
                summary += f"📉 売り：{ '、'.join(sell_signals) }"
            neutral_list.append(summary)

    # ✅ Slack通知
    send_signal_summary("📈 *買いシグナル銘柄*", buy_list)
    send_signal_summary("📉 *売りシグナル銘柄*", sell_list)
    send_signal_summary("🌀 *シグナル混在（様子見）*", neutral_list)

# slack_notifier.py
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
client = WebClient(token=SLACK_BOT_TOKEN)

def send_summary_with_files(buy_csv_path, sell_csv_path, buy_count, sell_count, date_str):
    """
    Slackにサマリー＋CSVファイル2つを送信
    """
    message = f"""📊 *{date_str} シグナルサマリー*
• 📈 買い銘柄：{buy_count}件（添付参照）
• 📉 売り銘柄：{sell_count}件（添付参照）
"""

    try:
        # メッセージ送信
        client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=message)

        # ファイルアップロード（買い）
        if os.path.exists(buy_csv_path):
            client.files_upload_v2(
                channel=SLACK_CHANNEL_ID,
                file=buy_csv_path,
                title=f"買い銘柄一覧（{date_str}）",
                filename=os.path.basename(buy_csv_path)
            )

        # ファイルアップロード（売り）
        if os.path.exists(sell_csv_path):
            client.files_upload_v2(
                channel=SLACK_CHANNEL_ID,
                file=sell_csv_path,
                title=f"売り銘柄一覧（{date_str}）",
                filename=os.path.basename(sell_csv_path)
            )

        print("✅ Slack通知 + ファイル添付 成功")

    except SlackApiError as e:
        print(f"❌ Slack送信失敗: {e.response['error']}")
