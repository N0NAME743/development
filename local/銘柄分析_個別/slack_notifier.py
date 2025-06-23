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
