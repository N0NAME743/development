# ================================
# Sec1｜セットアップ
# ================================

!pip install --upgrade gspread gspread_dataframe google-auth yfinance --quiet
!pip install ta --quiet

import os
import pandas as pd
import yfinance as yf
import gspread
from google.colab import auth
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from google.auth.transport.requests import Request
from datetime import datetime, timezone, timedelta
import google.auth
from google.colab import drive
import time
from collections import defaultdict

pd.set_option('future.no_silent_downcasting', True)

# ================================
# Sec2｜定義・関数
# ================================

import numpy as np

SAVE_PATH = "drive/MyDrive/ColabNotebooks/銘柄分析/signal"  # 🔧 保存先のパスを正しく設定
BACKUP_SUBFOLDER = "backup"  # 🔧 バックアップはこのサブフォルダに

# GoogleDrive関数
def mount_drive():
    drive.mount('/content/drive')

def authenticate_services():
    auth.authenticate_user()
    creds, _ = google.auth.default()
    return creds, gspread.authorize(creds), creds

def get_drive_folder_id_by_path(path, creds):
    service = build('drive', 'v3', credentials=creds)
    parts = path.strip("/").split("/")
    parent_id = 'root'
    for part in parts:
        query = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        if files:
            parent_id = files[0]['id']
        else:
            file_metadata = {
                'name': part,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            file = service.files().create(body=file_metadata, fields='id').execute()
            parent_id = file['id']
    return parent_id, service

def delete_existing_file_by_name(drive_service, folder_id, file_name):
    query = f"'{folder_id}' in parents and name = '{file_name}' and mimeType = 'application/vnd.google-apps.spreadsheet'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    for file in files:
        drive_service.files().delete(fileId=file['id']).execute()

def create_spreadsheet_in_folder(title, folder_id, creds):
    drive_service = build("drive", "v3", credentials=creds)
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id]
    }
    file = drive_service.files().create(body=file_metadata, fields="id").execute()
    return file["id"]

# 日付の取得
def get_today_str():
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %H:%M:%S")

# スプレッドシートのColum
def reorder_columns(df, preferred_order):
    existing_cols = [col for col in preferred_order if col in df.columns]
    other_cols = [col for col in df.columns if col not in existing_cols]
    return df[existing_cols + other_cols]

def symbol_to_num(symbol):
    # .Tを除去し、数値部分のみ抽出
    s = str(symbol).replace('.T', '')
    try:
        return int(float(s))
    except ValueError:
        return np.nan  # 数値化できない場合はNaN

def clean_dataframe_columns(df, expected_cols):
    """
    DataFrameから重複列（例: 'MultiSign.1'）を取り除き、列順をexpected_colsに整える。
    """
    # 1. 期待される列名に対して、.1 や .2 がついた重複列があれば削除
    deduped_cols = {}
    for col in df.columns:
        base_col = col.split('.')[0]
        if base_col not in deduped_cols:
            deduped_cols[base_col] = col  # 最初に出てきた正規名を採用

    df = df[list(deduped_cols.values())]

    # 2. 列順をexpected_colsの順に整える（存在する列のみ）
    df = df[[col for col in expected_cols if col in df.columns]]

    return df

def normalize_symbol_column(df):
    """
    Symbol列を "XXXX.T" 形式に統一する
    - float形式の .0 除去
    - .T の重複除去
    - .0.T の誤変換除去
    """
    def clean_symbol(val):
        try:
            val = str(val).strip().replace('$', '')
            val = val.replace('.0.T', '')  # ← 追加ポイント
            if val.endswith('.0'):
                val = val[:-2]
            val = val.replace('.T', '')  # 重複除去
            return val + '.T'
        except:
            return ""

    if "Symbol" in df.columns:
        df["Symbol"] = df["Symbol"].apply(clean_symbol)
    return df

import pandas as pd
import numpy as np
from ta.trend import ADXIndicator, MACD
from ta.momentum import RSIIndicator

def detect_candlestick_patterns(df):
    """ローソク足の形状に基づいてシンプルなパターンを検出する"""
    patterns = []

    open_ = df["Open"].iloc[-1]
    close = df["Close"].iloc[-1]
    high = df["High"].iloc[-1]
    low = df["Low"].iloc[-1]

    body = abs(close - open_)
    upper_shadow = high - max(open_, close)
    lower_shadow = min(open_, close) - low

    # 下髭陽線：陽線かつ長い下ヒゲ
    if close > open_ and lower_shadow > body * 2:
        patterns.append("下髭陽線")

    # 陽の丸坊主：陽線で上下ヒゲが非常に短い
    if close > open_ and upper_shadow < body * 0.1 and lower_shadow < body * 0.1:
        patterns.append("陽の丸坊主")

    return patterns

def detect_multi_candle_patterns(df):
    """複数日のローソク足形状に基づくパターンを検出"""
    patterns = []

    if len(df) < 5:
        return patterns  # 過去3日必要

    # 直近3日のデータ
    last3 = df.iloc[-3:]
    open_ = last3["Open"]
    close = last3["Close"]
    high = last3["High"]
    low = last3["Low"]

    # 三連続陽線
    if all(close.values > open_.values):
        patterns.append("三連続陽線")

    # 三空踏み上げ（連続で上方向に窓を開けて始まる）
    gaps = [
        open_.iloc[1] > high.iloc[0],
        open_.iloc[2] > high.iloc[1]
    ]
    if all(gaps):
        patterns.append("三空踏み上げ")

    return patterns

def is_ath_breakout(df):
    """終値が上場来高値付近にあるか判定"""
    recent_high = df["High"].max()
    return df["Close"].iloc[-1] >= recent_high * 0.995

def analyze_stock(df):
    try:
        if len(df) < 30:
            raise ValueError("データ不足")

        df = df.copy()
        close = df["Close"]
        open_ = df["Open"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        df["MA5"] = close.rolling(5).mean()
        df["MA25"] = close.rolling(25).mean()
        df["RSI"] = RSIIndicator(close, window=14).rsi()
        macd = MACD(close)
        df["MACD"] = macd.macd()
        df["MACD_signal"] = macd.macd_signal()
        adx = ADXIndicator(high, low, close, window=14)
        df["ADX"] = adx.adx()

        rsi_last = df["RSI"].iloc[-1]
        adx_last = df["ADX"].iloc[-1]
        close_now = close.iloc[-1]
        close_prev = close.iloc[-2]
        open_now = open_.iloc[-1]
        high_prev = high.iloc[-2]
        low_prev = low.iloc[-2]
        ma5_prev = df["MA5"].iloc[-2]
        ma25_prev = df["MA25"].iloc[-2]
        ma5_now = df["MA5"].iloc[-1]
        ma25_now = df["MA25"].iloc[-1]
        ma25 = ma25_now

        disparity = ((close_now - ma25) / ma25) * 100 if ma25 else 0

        signals = []

        # === シグナル検出 ===
        if df["MACD"].iloc[-2] < df["MACD_signal"].iloc[-2] and df["MACD"].iloc[-1] > df["MACD_signal"].iloc[-1]:
            signals.append("MACD陽転")
        if df["MACD"].iloc[-2] > df["MACD_signal"].iloc[-2] and df["MACD"].iloc[-1] < df["MACD_signal"].iloc[-1]:
            signals.append("MACD陰転")

        if ma5_prev < ma25_prev and ma5_now > ma25_now:
            signals.append("短期ゴールデンクロス")
        if ma5_prev > ma25_prev and ma5_now < ma25_now:
            signals.append("短期デッドクロス")

        if df["RSI"].iloc[-2] < 30 and rsi_last > 30:
            signals.append("RSI反発")
        if df["RSI"].iloc[-2] > 70 and rsi_last < 70:
            signals.append("RSI過熱反転")

        recent_high = df["High"].iloc[-20:-1].max()
        if close_now > recent_high:
            signals.append("直近高値突破")
        elif close_now < recent_high * 0.98:
            signals.append("高値反落")

        if volume.iloc[-1] > volume.rolling(5).mean().iloc[-2] * 1.5:
            signals.append("出来高↑")

        if open_now > high_prev:
            signals.append("窓開け上昇")
        elif open_now < low_prev:
            signals.append("窓開け下落")

        pct_change = ((close_now - close_prev) / close_prev) * 100
        if pct_change >= 7:
            signals.append("急騰")
        elif pct_change <= -7:
            signals.append("急落")

        if close_now >= df["High"].max() * 0.995:
            signals.append("上場来高値突破")

        signals.extend(detect_candlestick_patterns(df))
        signals.extend(detect_multi_candle_patterns(df))

        # ⭐ 注目度判定（スコアではなくsignalsに基づく）
        def judge_attention(signals):
            keywords = {
                "★★★": ["三空踏み上げ", "上場来高値", "直近高値突破"],
                "★★": ["三連続陽線", "MACD陽転", "短期ゴールデンクロス", "出来高↑"],
                "★": ["RSI反発", "窓開け上昇"]
            }
            for star, keys in keywords.items():
                if any(k in signals for k in keys):
                    return star
            return ""

        attention_flag = judge_attention(signals)

        # トレンド分類（スコアに関係なく残してOK）
        if adx_last >= 40:
            trend = "強トレンド"
        elif adx_last >= 25:
            trend = "中トレンド"
        else:
            trend = "弱トレンド"

        return signals, adx_last, trend, rsi_last, disparity, attention_flag

    except Exception as e:
        print(f"❌ analyze_stock エラー: {e}")
        return [], None, "不明", 0.0, None, ""

# Comment判定
# 分析判定@2025-06-11.売り判定も追加
def format_signals_to_comment(signals, adx_value=None):
    phrases = []
    warnings = []

    # ===== 買い傾向コメント =====
    if "MACD陽転" in signals:
        phrases.append("MACDが陽転し、買いの勢いが出始めています。")
    if "短期ゴールデンクロス" in signals:
        phrases.append("短期の移動平均線がゴールデンクロスを形成しています。")
    if "RSI反発" in signals:
        phrases.append("RSIが反発し、反転上昇の兆しがあります。")
    if "出来高↑" in signals:
        phrases.append("出来高が急増しており注目が集まっています。")
    if "直近高値突破" in signals:
        phrases.append("直近の高値をブレイクし、トレンド継続が期待されます。")
    if "三連続陽線" in signals:
        phrases.append("3日連続の陽線が続いており、強い上昇圧力が確認できます。")
    if "三空踏み上げ" in signals:
        phrases.append("三空踏み上げが出現しており、強い買い相場の継続が示唆されます。")

    # ===== 売り・注意シグナルコメント =====
    if "MACD陰転" in signals:
        warnings.append("MACDが陰転し、下落転換の兆しがあります。")
    if "短期デッドクロス" in signals:
        warnings.append("短期デッドクロスが発生し、下落リスクに注意が必要です。")
    if "RSI過熱反転" in signals:
        warnings.append("RSIが過熱圏から反転しており、利確や調整のタイミングかもしれません。")
    if "高値反落" in signals:
        warnings.append("高値更新に失敗しており、反落の可能性があります。")
    if "三空踏み上げ" in signals:
        warnings.append("ただし三空踏み上げは過熱の兆候ともされ、押し目や反落には警戒が必要です。")

    # ===== トレンド強度（ADX）コメント =====
    if adx_value is not None:
        if adx_value >= 40:
            phrases.append("トレンドは非常に強く、流れに乗る戦略が有効です。")
        elif adx_value >= 25:
            phrases.append("中程度のトレンドが継続しています。")

    # ===== コメント文生成 =====
    final_comment = " ".join(phrases + warnings)
    return final_comment

def judge_action_by_comment(comment: str) -> str:
    """
    コメント内容から、Action列（買い/中立/売り）を判定する
    """
    buy_keywords = ["買い", "反発", "上昇", "ブレイク", "陽線", "注目"]
    sell_keywords = ["デッドクロス", "陰転", "下落", "過熱", "反落", "利確", "警戒"]

    comment_lower = comment.lower()

    buy_score = sum(1 for k in buy_keywords if k in comment)
    sell_score = sum(1 for k in sell_keywords if k in comment)

    if buy_score > 1 and sell_score == 0:
        return "買い（エントリー検討）"
    elif sell_score > 1 and buy_score == 0:
        return "売り（利確/調整）"
    else:
        return "中立（様子見）"

def process_all_sheets(spreadsheet_name, gc, drive_service, folder_id_main, folder_id_backup, creds):
    sheet_process_logs = []
    global SAVE_PATH
    today_str, timestamp_str = get_today_str()
    spreadsheet = gc.open(spreadsheet_name)
    sheet_list = spreadsheet.worksheets()

    all_dfs = []  # 各シートのDFを格納

    for worksheet in sheet_list:
        start_time_sheet = time.time()
        sheet_name = worksheet.title
        print(f"\U0001f50d 処理中: {sheet_name}")
        df = get_as_dataframe(worksheet, evaluate_formulas=True)

        if "Symbol" not in df.columns:
            print(f"⚠️ {sheet_name} にSymbol列がありません。スキップします。")
            continue

        for col in ["Name", "Time", "Price", "Sign", "MultiSign", "Action", "注目度"]:
            if col not in df.columns:
                df[col] = pd.Series([""] * len(df), dtype="object")
            else:
                df[col] = df[col].astype("object")

        df["Time"] = df["Time"].astype(str)

        for i, row in df.iterrows():
            if i % 100 == 0:
                print(f"   🔄 {i+1}件目を処理中...")
            raw_symbol = None
            try:
                raw_symbol = str(row["Symbol"]).strip().replace("$", "").replace(".T", "")
                if "." in raw_symbol:
                    raw_symbol = raw_symbol.split(".")[0]
                code = raw_symbol.zfill(4)
                ticker = f"{code}.T"

                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                if hist.empty or len(hist) < 30:
                    print(f"⚠️ データ不足: {ticker} - ヒストリカルデータ{len(hist)}件")
                    continue

                df.at[i, "Price"] = round(hist["Close"].iloc[-1], 2)
                if pd.isnull(row["Name"]) or row["Name"] == "":
                    df.at[i, "Name"] = stock.info.get("shortName", "")

                signals, adx_last, trend, rsi_last, disparity, attention_flag = analyze_stock(hist)
                df.at[i, "Sign"] = "✅ " + ", ".join(signals) if signals else ""
                comment = format_signals_to_comment(signals, adx_last)
                df.at[i, "MultiSign"] = comment
                df.at[i, "Action"] = judge_action_by_comment(comment)
                df.at[i, "Time"] = timestamp_str
                df.at[i, "注目度"] = attention_flag

            except Exception as e:
                print(f"⚠️ エラー: {raw_symbol or '不明'} - {e}")

        # Symbol列を正規化する
        df = normalize_symbol_column(df)

        df = reorder_columns(df, ["Symbol", "Name", "Time", "Price", "注目度", "Action", "Sign", "MultiSign"])
        df = clean_dataframe_columns(df, ["Symbol", "Name", "Time", "Price", "注目度", "Action", "Sign", "MultiSign"])

        all_dfs.append(df.copy())

        df.drop(columns=[col for col in ["TrendScore", "TrendScore_raw"] if col in df.columns], inplace=True)
        worksheet.clear()
        set_with_dataframe(worksheet, df.fillna("").infer_objects(copy=False))

        new_sheet_title = f"Watchlist_{sheet_name}_{today_str}"
        try:
            delete_existing_file_by_name(drive_service, folder_id_backup, new_sheet_title)
            new_spreadsheet = gc.create(new_sheet_title, folder_id_backup)
            set_with_dataframe(new_spreadsheet.sheet1, df.fillna("").infer_objects(copy=False))
            print(f"✅ 完了: {new_sheet_title}")
        except Exception as e:
            print(f"❌ 作成失敗: {new_sheet_title} - {e}")

        elapsed_sheet = time.time() - start_time_sheet
        sheet_process_logs.append({
            "sheet_name": sheet_name,
            "count": len(df),
            "elapsed": elapsed_sheet,
            "failures": [row["Symbol"] for i, row in df.iterrows() if "エラー" in str(row["MultiSign"]) or "取得失敗" in str(row["Name"])]
        })

    # ✅ 条件一致銘柄の統合と出力
    try:
        combined_df = pd.concat(all_dfs, ignore_index=True)

        # ✅ Signal数をカウント
        combined_df["SignalCount"] = combined_df["Sign"].apply(
            lambda x: x.count(",") + 1 if isinstance(x, str) and x.startswith("✅") else 0
        )

        # ✅ 条件一致: Actionまたは注目度 + Signalが3個以上
        condition = (
            ((combined_df["Action"] == "買い（エントリー検討）") | (combined_df["注目度"] == "★★★"))
            & (combined_df["SignalCount"] >= 3)
        )
        filtered_df = combined_df[condition].copy()
        filtered_df.drop(columns=["SignalCount"], inplace=True)

        # ✅ ソートと出力処理
        filtered_df["SortKey"] = filtered_df["Symbol"].apply(symbol_to_num)
        filtered_df.sort_values("SortKey", inplace=True)
        filtered_df.drop(columns=["SortKey"], inplace=True)

        summary_title = f"watchlist_signal_{today_str}"
        delete_existing_file_by_name(drive_service, folder_id_main, summary_title)
        summary_sheet_id = create_spreadsheet_in_folder(summary_title, folder_id_main, creds)
        summary_sheet = gc.open_by_key(summary_sheet_id)
        set_with_dataframe(summary_sheet.sheet1, filtered_df.fillna("").infer_objects(copy=False))

        sheet_url = f"https://docs.google.com/spreadsheets/d/{summary_sheet_id}/edit"
        print(f"📤 条件一致シグナル出力完了: {summary_title}")
        print(f"🔗 出力先URL: {sheet_url}")

    except Exception as e:
        print(f"⚠️ 条件一致の出力失敗: {e}")

    # === デバッグ出力 ===
    print("\n🔬 デバッグ情報:")
    print(f"全シート数: {len(sheet_list)}")
    print(f"処理済みシート数: {len(all_dfs)}")
    print(f"全データ件数: {len(combined_df)}")
    print(f"フィルタ後件数: {len(filtered_df)}")
    print(f"📁 保存先フォルダID（main）: {folder_id_main}")
    print("🎉 すべての処理が完了しました")

def create_spreadsheet_in_folder(title, folder_id, creds):
    drive_service = build("drive", "v3", credentials=creds)
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id]
    }
    file = drive_service.files().create(body=file_metadata, fields="id").execute()
    return file["id"]


# ================================
# ✅ メイン処理関数
# ================================

def main():
    # あなたのDrive上の目的フォルダIDに差し替えてください
    FOLDER_ID_MAIN = "1dFuJfNLSJ7tw43Ac9RKAqJ0yW49cLsIe"       # ColabNotebooks/銘柄分析/Watchlist
    FOLDER_ID_BACKUP = "1hN6fzMeT1ZB7I0jVRc9L_8HKIqI0Gi_W"     # ColabNotebooks/銘柄分析/Watchlist/backup

    spreadsheet_name = "watchlist"
    mount_drive()

    start_time = time.time()
    print("🚀 処理開始")

    global sheet_process_logs
    sheet_process_logs = []  # ← ログ初期化

    try:
        _, gc, creds = authenticate_services()

        # Google Drive APIのサービスオブジェクト
        drive_service = build("drive", "v3", credentials=creds)

        # 📌 フォルダIDをそのまま渡す（get_drive_folder_id_by_path を使わない）
        process_all_sheets(spreadsheet_name, gc, drive_service, FOLDER_ID_MAIN, FOLDER_ID_BACKUP, creds)

    except Exception as e:
        print(f"❌ 重大エラー: {e}")
        return

    elapsed = time.time() - start_time
    print("✅ 全処理完了！")
    print(f"⏱️ 所要時間: {elapsed:.1f} 秒")

    # 各シート単位のログ出力（省略せず出す）
    if sheet_process_logs:
        print("\n📊 シートごとの処理概要:")
        for log in sheet_process_logs:
            print(f"\n📄 シート: {log['sheet_name']}")
            print(f" - 件数: {log['count']} 行")
            print(f" - 処理時間: {log['elapsed']:.1f} 秒")
            if log['failures']:
                print(f" - ⚠️ 失敗銘柄: {len(log['failures'])} 件")
                from collections import defaultdict
                grouped = defaultdict(list)
                for code in log['failures']:
                    try:
                        prefix = int(code) // 1000 * 1000
                        grouped[f"{prefix}番台"].append(code)
                    except:
                        grouped["不明"].append(code)
                for group in sorted(grouped.keys()):
                    print(f"   ・{group}: [{', '.join(grouped[group])}]")
            else:
                print(" - 🎉 全銘柄正常に取得")
