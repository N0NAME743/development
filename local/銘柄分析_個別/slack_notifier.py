# slack_notifier.py｜Slack通知（Bot API＋CSV添付対応）

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from datetime import datetime

# .envファイルからトークン等を取得
load_dotenv()
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
client = WebClient(token=SLACK_BOT_TOKEN)

def send_summary_with_files(buy_csv_path, sell_csv_path, buy_count, sell_count, date_str):
    """
    SlackにシグナルサマリーとCSVファイル（買い/売り）を添付して送信。
    """
    message = f"""📊 *{date_str} シグナルサマリー*
• 📈 買い銘柄：{buy_count}件（添付参照）
• 📉 売り銘柄：{sell_count}件（添付参照）
"""
    try:
        # テキストメッセージ送信
        client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=message)

        # ファイルアップロード：買い
        if os.path.exists(buy_csv_path):
            client.files_upload_v2(
                channel=SLACK_CHANNEL_ID,
                file=buy_csv_path,
                title=f"買い銘柄一覧（{date_str}）",
                filename=os.path.basename(buy_csv_path)
            )

        # ファイルアップロード：売り
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

def notify_signal_alerts_from_uploaded(uploaded_today):
    """
    アップロードされた銘柄からシグナルを分類（買い・売り・混在）して集約表示。
    ※ 通知は行わず、後続ロジックでファイル添付付き通知を行うことを想定。
    """
    buy_list, sell_list, neutral_list = [], [], []

    for entry in uploaded_today:
        symbol = entry["symbol"]
        name = entry["name"]
        attention = entry.get("attention", "")
        signals = entry.get("signals", {})

        buy_signals = signals.get("buy", [])
        sell_signals = signals.get("sell", [])
        total_signals = len(buy_signals) + len(sell_signals)

        def format_entry(symbol, name, attention, label, sigs):
            return f"{symbol}（{name}）: {attention} | 💡 {label}：{'、'.join(sigs)}"

        if len(buy_signals) >= 3:
            buy_list.append(format_entry(symbol, name, attention, "買い", buy_signals))
        elif len(sell_signals) >= 3:
            sell_list.append(format_entry(symbol, name, attention, "売り", sell_signals))
        elif total_signals >= 4:
            neutral_list.append(format_entry(symbol, name, attention, "混在", buy_signals + sell_signals))

    # ログ出力のみ（通知は別関数）
    #if not buy_list:
    #     print("🚫 通知対象なし: 📈 *買いシグナル銘柄*")
    #if not sell_list:
    #     print("🚫 通知対象なし: 📉 *売りシグナル銘柄*")
    #if not neutral_list:
    #     print("🚫 通知対象なし: 🌀 *シグナル混在（様子見）*")