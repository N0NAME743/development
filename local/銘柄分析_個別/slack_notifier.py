# ==============================
# Sec｜slack_notifier.py
# ==============================

import requests

def send_to_slack(webhook_url, message):
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("✅ Slack通知送信成功")
        else:
            print(f"❌ Slack通知失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Slack通知中にエラー発生: {e}")
