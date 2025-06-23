from slack_sdk import WebClient
import os
from dotenv import load_dotenv

load_dotenv()
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

client.chat_postMessage(channel=os.getenv("SLACK_CHANNEL_ID"), text="✅ Slack Bot連携テストです！")
