
#追加内容
##仕手株と思われる銘柄の警戒機能#
##高値突破判定	「直近60日高値」＋「期間内の高値を本当に超えたときのみ」判定
##急騰履歴検出	直近60日で+40%以上の変動のみ警告
##小型株判定	時価総額100億円未満のみに限定し、過剰検出を防止
##スコア加点シグナルの複数追加
##週別評価分析コードの追加

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

import yfinance as yf

# 株価データと会社名を取得する関数
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        name = info.get("shortName", symbol)

        df = yf.download(symbol, period="18mo", interval="1d", auto_adjust=False)

        if df.empty:
            raise ValueError("取得結果が空です")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).astype(float)
        df.index.name = "Date"
        return df, name

    except Exception as e:
        print(f"❌ データ取得エラー: {symbol} - {e}")
        return pd.DataFrame(), symbol

# ================================
# 完全統合スクリプト（定義 + 出力対応）
# ================================

import pandas as pd
import numpy as np
from ta.trend import ADXIndicator, MACD
from ta.momentum import RSIIndicator

# スコア辞書（注目度・コメント・点数）
LEVELS = {
    "★★★": {
        "keywords": [
            {"text": "上場来高値突破", "comment": "上場来高値を更新し注目度MAX"},
            {"text": "直近高値突破", "comment": "直近高値を突破し、トレンド継続の可能性"},
            {"text": "出来高急増", "comment": "出来高が急増し、大口の買いが入っている可能性"},
            {"text": "期間内高値更新（要注目）", "comment": "取得可能期間内の最高値を更新しており、注目度は高いです。"},
            {"text": "週足高値ブレイク", "comment": "週足でも高値を更新しており、中長期的な強さが伺えます。"},
            {"text": "MACD週足陽転", "comment": "週足ベースのMACDが陽転し、中長期で買いの勢いが出ています。"}
        ],
        "score": 3
    },
    "★★": {
        "keywords": [
            {"text": "MACD陽転", "comment": "MACDが陽転し、買いの勢いが出始めています。"},
            {"text": "短期ゴールデンクロス", "comment": "短期の移動平均線がゴールデンクロスを形成しています。"},
            {"text": "中期ゴールデンクロス", "comment": "中期の移動平均線もゴールデンクロスし、トレンドの持続性が高まっています。"},
            {"text": "RSI反発", "comment": "RSIが反発し、反転上昇の兆しがあります。"},
            {"text": "出来高↑", "comment": "出来高が増えており注目が集まっています。"},
            {"text": "三連続陽線", "comment": "3日連続の陽線が続いており、強い上昇圧力が確認できます。"},
            {"text": "陽の丸坊主", "comment": "陽の丸坊主が出現し、買い圧力の強さを示しています。"},
            {"text": "下値切り上げ継続", "comment": "安値が切り上がる展開が続いており、下支えの強さが見られます。"}
        ],
        "score": 2
    },
    "★": {
        "keywords": [
            {"text": "窓開け上昇", "comment": "窓を開けて上昇し勢いあり"},
            {"text": "下髭陽線", "comment": "下髭陽線が出現し、押し目買いの可能性あり"},
            {"text": "押し目陽線", "comment": "調整後の押し目で陽線が出ており、反発の兆候が見られます。"},
            {"text": "上昇トレンドライン反発", "comment": "上昇トレンドライン付近で反発しており、下値支持が確認できます。"}
        ],
        "score": 1
    }
}

def adjust_attention_by_warning(attention, comment):
    """
    警戒ワードが含まれていれば、注目度を★→☆に1段階変換する
    """
    warning_keywords = ["仕手", "過熱", "注意", "警戒", "信用倍率高", "上髭陰線", "超小型株"]
    if any(k in comment for k in warning_keywords):
        if attention == "★★★":
            return "★★☆"
        elif attention == "★★":
            return "★☆"
        elif attention == "★":
            return "☆"
    return attention

# テクニカルコメント生成＆評価関数

import random

def get_summary_by_attention(attention):
    summaries = {
        "★": [
            "反転の兆しはあるものの、まだ明確なトレンドは形成されていません。",
            "やや買い圧力が見え始めましたが、様子見が妥当な場面です。",
            "初動の可能性もあるため、今後の展開に注視したい局面です。"
        ],
        "★★": [
            "複数のテクニカル指標が好転しており、打診買いを検討する余地があります。",
            "一定のトレンドシグナルが揃いはじめており、今後の上昇余地に注目です。",
            "過熱感には注意が必要ですが、反転局面に入った可能性があります。"
        ],
        "★★★": [
            "テクニカル的には買いサインが明確に揃っており、エントリーの好機と判断されます。",
            "強いトレンドが発生しており、大相場入りの可能性すら示唆されています。",
            "シグナルが複数一致し、買い勢力が優勢。仕込み時として有望です。"
        ],
        "ー": [
            "今のところ明確なトレンドは確認されていません。"
        ]
    }
    return "➡ 総評：" + random.choice(summaries.get(attention, summaries["ー"]))

def analyze_signals(signals, adx_value=None):
    total_score = 0
    comments = []

    # 重複シグナルの除去
    if "出来高↑" in signals and "出来高急増" in signals:
        signals = [s for s in signals if s != "出来高↑"]

    for level in LEVELS.values():
        for item in level["keywords"]:
            if item["text"] in signals:
                total_score += level["score"]
                comments.append(f"✅ {item['comment']}")

    if adx_value:
        if adx_value >= 40:
            total_score += 1
            comments.append("★強いトレンドが確認されており、順張りのタイミングとして有効です。")
        elif adx_value >= 25:
            comments.append("☆現在は中程度のトレンドが発生しており、方向感が出始めています。")

    # period_high 判定に High を含める処理を別途 analyze_stock 側で行う想定（この関数内には不要）

    if total_score >= 6:
        attention = "★★★"
    elif total_score >= 3:
        attention = "★★"
    elif total_score >= 1:
        attention = "★"
    else:
        attention = "ー"

    summary = get_summary_by_attention(attention)
    full_comment = "".join(comments + [summary])
    #score_str = f"{total_score:.1f} / 10.0"
    score_str = f"{total_score:.1f} / {max(total_score, 10):.1f}"  # ←変更ここ

    return attention, full_comment, total_score, score_str

# コメント内容からアクション判定（注目度ベース＋警告補正あり）
def judge_action_by_comment(comment, attention=None):
    if attention in ["★★★", "★★☆"]:
        return "買い（エントリー検討）"
    elif attention in ["★★", "★☆"]:
        return "買い（エントリー検討）"
    elif attention in ["★", "☆"]:
        return "中立（様子見）"
    else:
        return "中立（様子見）"

# ローソク足パターン簡易検出（任意追加可能）
def detect_candlestick_patterns(df):
    patterns = []
    open_, close, high, low = df.iloc[-1][["Open", "Close", "High", "Low"]]
    body = abs(close - open_)
    lower_shadow = min(open_, close) - low
    upper_shadow = high - max(open_, close)
    if close > open_ and lower_shadow > body * 2:
        patterns.append("下髭陽線")
    if close > open_ and upper_shadow < body * 0.1 and lower_shadow < body * 0.1:
        patterns.append("陽の丸坊主")
    return patterns

# === 週足シグナル検出 ===
def detect_weekly_signals(df):
    signals = []
    df_weekly = df.resample("W-FRI").last().dropna()
    if len(df_weekly) < 20:
        return signals

    # 週足高値ブレイク
    if df_weekly["Close"].iloc[-1] > df_weekly["High"].iloc[-20:-1].max():
        signals.append("週足高値ブレイク")

    # MACD週足陽転
    macd = MACD(df_weekly["Close"])
    macd_line = macd.macd()
    macd_signal = macd.macd_signal()
    if macd_line.iloc[-2] < macd_signal.iloc[-2] and macd_line.iloc[-1] > macd_signal.iloc[-1]:
        signals.append("MACD週足陽転")

    return signals

# === 中期GC検出 ===
def detect_mid_term_golden_cross(df):
    if len(df) < 75:
        return []
    ma25 = df["Close"].rolling(window=25).mean()
    ma75 = df["Close"].rolling(window=75).mean()
    cross = (ma25.shift(1) < ma75.shift(1)) & (ma25 > ma75)
    return ["中期ゴールデンクロス"] if cross.iloc[-1] else []

# === 押し目陽線検出 ===
def detect_pullback_bounce(df):
    if len(df) < 3:
        return []
    high_break = df["Close"].iloc[-3] > df["High"].iloc[-20:-4].max()
    pullback = df["Close"].iloc[-2] < df["Close"].iloc[-3]
    rebound = df["Close"].iloc[-1] > df["Open"].iloc[-1]
    if high_break and pullback and rebound:
        return ["押し目陽線"]
    return []

# === トレンドライン反発検出 ===
def detect_trendline_bounce(df):
    if len(df) < 10:
        return []
    lows = df["Low"].iloc[-10:]
    x = np.arange(len(lows))
    coef = np.polyfit(x, lows, 1)
    trendline = coef[0] * x + coef[1]
    if lows.iloc[-1] > trendline[-1]:
        return ["上昇トレンドライン反発"]
    return []

# === 下値切り上げ検出 ===
def detect_higher_lows(df):
    if len(df) < 3:
        return []
    lows = df["Low"].iloc[-3:]
    if lows.iloc[0] < lows.iloc[1] < lows.iloc[2]:
        return ["下値切り上げ継続"]
    return []

# ✅ analyze_stock() 関数（仕手株リスク＋高値突破修正済み）
def analyze_stock(df, info=None):
    if len(df) < 30:
        return [], "ー", "", "中立（様子見）", 0, ""

    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    open_ = df["Open"]
    volume = df["Volume"]

    # テクニカル指標
    df["RSI"] = RSIIndicator(close, window=14).rsi()
    macd = MACD(close)
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    adx = ADXIndicator(high, low, close, window=14)
    df["ADX"] = adx.adx()

    signals = []

    # テクニカルシグナル
    if df["MACD"].iloc[-2] < df["MACD_signal"].iloc[-2] and df["MACD"].iloc[-1] > df["MACD_signal"].iloc[-1]:
        signals.append("MACD陽転")
    if df["RSI"].iloc[-2] < 30 and df["RSI"].iloc[-1] > 30:
        signals.append("RSI反発")
    if volume.iloc[-1] > volume.rolling(5).mean().iloc[-2] * 1.5:
        signals.append("出来高↑")
    if volume.iloc[-1] > volume.rolling(5).mean().iloc[-2] * 2.0:
        signals.append("出来高急増")

    # 直近60営業日高値ブレイク
    recent_high = df["High"].iloc[-60:-1].max()
    if close.iloc[-1] > recent_high:
        signals.append("直近高値突破")

    # Highを含む期間内高値判定
    period_high = df["High"].max()
    if max(close.iloc[-1], high.iloc[-1]) > period_high:
        signals.append("期間内高値更新（要注目）")

    # ローソク足・危険パターン
    signals += detect_candlestick_patterns(df)
    signals += detect_danger_signals(df)

    # 急騰履歴
    spike_flag = detect_spike_history(df, threshold=0.4)
    if spike_flag:
        signals.append(spike_flag)

    # ファンダメンタル警告
    if info:
        signals += detect_risky_fundamentals(info)

    # 新規追加シグナルの統合
    signals += detect_weekly_signals(df)
    signals += detect_mid_term_golden_cross(df)
    signals += detect_pullback_bounce(df)
    signals += detect_trendline_bounce(df)
    signals += detect_higher_lows(df)

    adx_last = df["ADX"].iloc[-1]
    attention, comment, score, score_str = analyze_signals(signals, adx_last)
    
    # ⭐ 警戒コメントをもとに注目度を調整
    adjusted_attention = adjust_attention_by_warning(attention, comment)
    action = judge_action_by_comment(comment, adjusted_attention)

    return signals, adjusted_attention, comment, action, score_str

# 追加関数群

def detect_danger_signals(df):
    signals = []
    open_, close, high, low = df.iloc[-1][["Open", "Close", "High", "Low"]]
    body = abs(close - open_)
    upper_shadow = high - max(open_, close)
    if upper_shadow > body * 2 and close < open_:
        signals.append("上髭陰線（警戒）")
    return signals

# 修正版：急騰履歴判定（40%以上 + 直近60日間）
def detect_spike_history(df, threshold=0.4):
    recent_df = df[-60:]
    max_close = recent_df["Close"].max()
    min_close = recent_df["Close"].min()
    if (max_close - min_close) / min_close >= threshold:
        return "急騰履歴あり（仕手注意）"
    return ""

# 修正版：時価総額100億未満を警告（信用倍率含む）
def detect_risky_fundamentals(info):
    warnings = []
    if info.get("marketCap", 1e12) < 10_000_000_000:
        warnings.append("超小型株（注意）")
    if info.get("shortRatio", 0) > 3.0:
        warnings.append("信用倍率高（過熱感）")
    return warnings

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

        # 修正：既存列の型を object に変更
        for col in ["Name", "Time", "Price", "Action", "注目度", "Score", "Sign", "MultiSign"]:
            if col not in df.columns:
                df[col] = pd.Series([""] * len(df), dtype="object")
            else:
                df[col] = df[col].astype("object")

        df["Time"] = df["Time"].astype(str)

        # 🔁 ループ内
        total = len(df)
        start_time_loop = time.time()  # 🔄 全体の開始時間

        for i, row in df.iterrows():
            if i % 100 == 0:
                elapsed = time.time() - start_time_loop
                avg_time_per_row = elapsed / (i + 1) if i > 0 else 0
                remaining = avg_time_per_row * (total - i)
                print(f"   🔄 {i+1}件目を処理中... ⏱️ 経過: {elapsed:.1f}s｜残り予測: {remaining:.1f}s")

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
                    df.at[i, "Name"] = stock.info.get("shortName", "取得失敗")

                # ✅ 統合版 analyze_stock 関数に対応
                info = stock.info  # ← 追加
                signals, attention, comment, action, score_str = analyze_stock(hist, info)  # ← 引数にinfoを追加

                df.at[i, "Sign"] = "✅ " + ", ".join(signals) if signals else ""
                df.at[i, "MultiSign"] = comment
                df.at[i, "Action"] = action
                df.at[i, "注目度"] = attention if attention else "ー"
                df.at[i, "Score"] = score_str
                df.at[i, "Time"] = timestamp_str

            except Exception as e:
                print(f"⚠️ エラー: {raw_symbol or '不明'} - {e}")

        # Symbol列を正規化する
        df = normalize_symbol_column(df)

        df = reorder_columns(df, ["Symbol", "Name", "Time", "Price", "Action", "Score", "注目度", "Sign", "MultiSign"])
        df = clean_dataframe_columns(df, ["Symbol", "Name", "Time", "Price","Action", "Score","注目度", "Sign", "MultiSign"])

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

        # ✅ 条件一致: Actionまたは注目度 + Signalが3個以上 + スコア5.0以上
        condition = (
            ((combined_df["Action"] == "買い（エントリー検討）") | (combined_df["注目度"] == "★★★")) &
            (combined_df["SignalCount"] >= 3) &
            (combined_df["Score"].astype(str).str.extract(r"([\d\.]+)").astype(float)[0] >= 5.0)
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
    FOLDER_ID_BACKUP = "1hN6fzMeT1ZB7I0jVRc9L_8HKIqI0Gi_W"     # ColabNotebooks/銘柄分析/Watchlist/watchlist

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
