import os
import requests

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL") or "https://hooks.slack.com/services/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"
message = "✅ Slack通知テストです！（チャートBotより）"

payload = {"text": message}
r = requests.post(SLACK_WEBHOOK_URL, json=payload)

if r.status_code == 200:
    print("✅ 通知成功")
else:
    print(f"❌ 通知失敗: {r.status_code} - {r.text}")
