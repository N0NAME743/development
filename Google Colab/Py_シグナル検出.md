# ================================
# Sec1｜セットアップ
# ================================

!pip install --upgrade gspread gspread_dataframe google-auth yfinance --quiet

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

# ================================
# Sec2｜定義・関数
# ================================

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

# Comment判定
def format_signals_to_comment(signals, close=None, ma25=None, adx_value=None):
    phrases = []
    warnings = []
    score = 0

    # --- MACD + 出来高 ---
    if "MACD" in signals and "出来高↑" in signals:
        phrases.append("MACDが陽転し、出来高の増加とともに買い圧力の高まりが見られます。")
        score += 3
    elif "MACD" in signals:
        phrases.append("MACDが陽転し、短期的な上昇の兆しがあります。")
        score += 2

    # --- ゴールデンクロス ---
    if "5MA>25MA" in signals:
        phrases.append("移動平均線のゴールデンクロスが確認されました。")
        score += 2

    # --- RSI反発 ---
    if "RSI反発" in signals:
        if close is not None and ma25 is not None and close < ma25:
            phrases.append("RSIが反発しており、底打ちの可能性があります。")
        else:
            phrases.append("RSIが反発していますが、やや高値圏のため慎重に見極めたいところです。")
        score += 1.5

    # --- 高値突破 ---
    if "高値突破" in signals:
        phrases.append("直近高値をブレイクし、トレンド継続の可能性があります。")
        score += 2

    # --- ボックス・三角 ---
    if "ボックス相場" in signals:
        phrases.append("ボックス相場内の動きが続いており、レンジの上限や下限に注目が集まります。")
        score += 0.5
    if "三角保ち合い" in signals:
        phrases.append("三角保ち合いの形状を見せており、近いうちにブレイクする可能性があります。")
        score += 0.5

    # --- ADXの文脈評価 ---
    if adx_value is not None:
        if adx_value >= 40:
            if "MACD" in signals or "5MA>25MA" in signals:
                phrases.append("トレンドが非常に強く、買い圧力が継続しています。")
                score += 2
            else:
                warnings.append("ADXが高く、トレンドは強いですが新たな買いサインは限定的です。")
                score += 0.5
        elif adx_value >= 25:
            if "MACD" in signals or "5MA>25MA" in signals:
                phrases.append("中程度のトレンドに加え、テクニカル指標も好転しています。")
                score += 1.5
            else:
                warnings.append("ADXはやや高めですが、他のシグナルとの連動は弱めです。")
                score += 0.5

    # --- 乖離率の扱い ---
    for s in signals:
        if "乖離率" in s:
            try:
                val = float(s.replace("乖離率", "").replace("%", ""))
                if abs(val) >= 10:
                    warnings.append(f"{s} に達しており、過熱感があります。")
                    score += 0.5
                else:
                    phrases.append(f"{s} の状態です。")
                    score += 0.5
            except:
                continue

    # --- 出力処理 ---
    if not phrases and not warnings:
        return "明確な買いサインは見られません。", 0

    final_comment = " ".join(phrases)
    if warnings:
        final_comment += " " + " ".join(warnings)

    return final_comment, round(score, 1)

def analyze_stock(hist):
    signals = []
    trend = "不明"

    close = hist["Close"]
    ma5 = close.rolling(window=5).mean()
    ma25 = close.rolling(window=25).mean()
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9).mean()

    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_gain = up.rolling(window=14).mean()
    avg_loss = down.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    vol_ma5 = hist["Volume"].rolling(window=5).mean()
    max_high = close.rolling(window=20).max()

    high = close + 1.0
    low = close - 1.0
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean()
    plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=14).mean()

    range20 = close.rolling(window=20).max() - close.rolling(window=20).min()
    range_std = range20.rolling(window=5).std()

    # === シグナル抽出 ===
    if macd.iloc[-2] < signal_line.iloc[-2] and macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-1] > 0:
        signals.append("MACD")
    if ma5.iloc[-2] < ma25.iloc[-2] and ma5.iloc[-1] > ma25.iloc[-1] and close.iloc[-1] > ma25.iloc[-1]:
        signals.append("5MA>25MA")
    if rsi.iloc[-2] < 30 and rsi.iloc[-1] > 30 and rsi.iloc[-1] > rsi.iloc[-2] + 5:
        signals.append("RSI反発")
    if hist["Volume"].iloc[-1] > 1.5 * vol_ma5.iloc[-1] and hist["Volume"].iloc[-1] > hist["Volume"].iloc[-2]:
        signals.append("出来高↑")
    if close.iloc[-1] > max_high.iloc[-2] * 1.01:
        signals.append("高値突破")

    disparity = ((close.iloc[-1] - ma25.iloc[-1]) / ma25.iloc[-1]) * 100
    if abs(disparity) > 5:
        signals.append(f"乖離率{disparity:+.1f}%")
    if adx.iloc[-1] >= 40:
        signals.append("ADX強↑")
    elif adx.iloc[-1] >= 25:
        signals.append("ADX中↑")
    if range_std.iloc[-1] < 1.0:
        signals.append("ボックス相場")
    if range_std.iloc[-1] < 0.5 and not range_std.iloc[-2] < 0.5:
        signals.append("三角保ち合い")

    # === トレンド分類 ===
    adx_last = adx.iloc[-1] if not adx.empty else None
    if adx_last is not None:
        if adx_last < 20:
            trend = "横ばい"
        elif ("MACD" in signals or "5MA>25MA" in signals) and adx_last >= 25:
            trend = "上昇"
        else:
            trend = "不明"

    # ★ここで最新値を取得
    rsi_last = rsi.iloc[-1] if not rsi.empty else None
    # disparityはすでに計算済み

    score, overbought = calc_score(signals, adx_last, rsi_last, disparity)
    return signals, adx_last, trend, score, rsi_last, disparity, overbought

# スコア判定処理

def calc_score(signals, adx_value, rsi_value=None, disparity_value=None):
    score = 0.0
    # 既存の加点ロジック
    if "出来高↑" in signals:
        score += 1.0
    if "高値突破" in signals:
        score += 1.5
    has_disparity = any(
        "乖離率" in s and float(s.replace("乖離率", "").replace("%", "").replace("+", "")) >= 10
        for s in signals
    )
    if has_disparity:
        score += 1.0
    if adx_value is not None:
        if adx_value >= 40:
            score += 1.5
        elif adx_value >= 25:
            score += 1.0

    # --- 過熱感による減点 ---
    overbought = False
    if rsi_value is not None and rsi_value >= 70:
        score -= 1.0
        overbought = True
    if disparity_value is not None and abs(disparity_value) >= 10:
        score -= 1.0
        overbought = True

    return max(score, 0), overbought  # スコアは0未満にならないように

def judge_action_by_score(score):
    """
    スコアに応じてアクションを返す（3分類）
    0～1   ：「静観（エントリー非推奨）」
    2～3   ：「中立（慎重に検討）」
    4～5   ：「積極検討（買い目線強）」
    """
    if 4.0 <= score <= 5.0:
        return "積極検討（買い目線強）"
    elif 2.0 <= score < 4.0:
        return "中立（慎重に検討）"
    elif 0.0 <= score < 2.0:
        return "静観（エントリー非推奨）"
    else:
        return "スコア異常"

def analyze_trend_and_score(signals, adx_value):
    score = calc_score(signals, adx_value)
    # トレンド判定
    if 4.0 <= score <= 5.0:
        trend_label = "上昇トレンド"
    elif 2.0 <= score < 4.0:
        trend_label = "やや上昇傾向"
    elif 0.0 <= score < 2.0:
        trend_label = "横ばい〜警戒"
    else:
        trend_label = "トレンド不明"
    score_str = f"{round(score, 1)}/5.0"
    mark = "◯" if 4.0 <= score <= 5.0 else "✕"
    return trend_label, score_str, mark

def analyze_and_judge(hist, stock_name=""):
    signals, adx_last, trend, trend_score = analyze_stock(hist)
    score = calc_score(signals, adx_last)
    comment = format_signals_to_comment(signals,
                                        close=hist["Close"].iloc[-1],
                                        ma25=hist["Close"].rolling(window=25).mean().iloc[-1],
                                        adx_value=adx_last)[0]
    action = judge_action_by_score(score)
    print(f"【{stock_name}】")
    print(f"シグナル: {signals}")
    print(f"スコア: {score}/5.0")
    print(f"推奨アクション: {action}")
    print(f"コメント: {comment}")
    print("-" * 40)
    return {
        "stock": stock_name,
        "signals": signals,
        "score": score,
        "action": action,
        "comment": comment
    }

import numpy as np

def symbol_to_num(symbol):
    # .Tを除去し、数値部分のみ抽出
    s = str(symbol).replace('.T', '')
    try:
        return int(float(s))
    except ValueError:
        return np.nan  # 数値化できない場合はNaN

def process_all_sheets(spreadsheet_name, gc, drive_service, folder_id_main, folder_id_backup):
    global SAVE_PATH
    global sheet_process_logs
    today_str, timestamp_str = get_today_str()
    spreadsheet = gc.open(spreadsheet_name)
    sheet_list = spreadsheet.worksheets()

    all_dfs = []  # ← ここでリストを初期化

    for worksheet in sheet_list:
        start_time_sheet = time.time()  # ← ここで測定開始
        sheet_name = worksheet.title
        print(f"🔍 処理中: {sheet_name}")
        df = get_as_dataframe(worksheet, evaluate_formulas=True)

        if "Symbol" not in df.columns:
            print(f"⚠️ {sheet_name} にSymbol列がありません。スキップします。")
            continue

        # 列の初期化処理
        for col in ["Name", "Time", "Price", "TrendScore", "Sign", "MultiSign", "Action"]:
            if col not in df.columns:
                df[col] = pd.Series([""] * len(df), dtype="object")
            else:
                df[col] = df[col].astype("object")

        df["Time"] = df["Time"].astype(str)

        for i, row in df.iterrows():
            raw_symbol = None
            try:
                # シンボル前処理
                raw_symbol = str(row["Symbol"]).strip().replace("$", "").replace(".T", "")
                if "." in raw_symbol: raw_symbol = raw_symbol.split(".")[0]
                code = raw_symbol.zfill(4)
                ticker = f"{code}.T"

                # 株価データ取得
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                if hist.empty or len(hist) < 30:
                    print(f"⚠️ データ不足: {ticker} - ヒストリカルデータ{len(hist)}件")
                    continue

                # 基本情報更新
                df.at[i, "Price"] = round(hist["Close"].iloc[-1], 2)
                if pd.isnull(row["Name"]) or row["Name"] == "":
                    df.at[i, "Name"] = stock.info.get("shortName", "")

                # 分析処理
                signals, adx_last, trend, score, rsi_last, disparity, overbought = analyze_stock(hist)
                df.at[i, "Sign"] = "✅ " + ", ".join(signals) if signals else ""

                # コメント生成
                comment, _ = format_signals_to_comment(
                    signals,
                    close=hist["Close"].iloc[-1],
                    ma25=hist["Close"].rolling(25).mean().iloc[-1],
                    adx_value=adx_last  # ← adx_lastを使用
                )
                df.at[i, "MultiSign"] = comment
                df.at[i, "Time"] = timestamp_str

                # スコア計算とアクション判定
                score, overbought = calc_score(signals, adx_last, rsi_last, disparity)
                df.at[i, "TrendScore"] = round(score, 1)

                action = judge_action_by_score(score)
                if overbought and action == "積極検討（買い目線強）":
                    action = "中立（過熱感警戒）"
                df.at[i, "Action"] = action

            except Exception as e:
                print(f"⚠️ エラー: {raw_symbol or '不明'} - {e}")

        # データ整形
        df = reorder_columns(df, ["Symbol", "Name", "Time", "Price", "Action", "TrendScore", "Sign", "MultiSign"])
        df = clean_dataframe_columns(df, ["Symbol", "Name", "Time", "Price", "Action", "TrendScore", "Sign", "MultiSign"])
        df["Symbol"] = df["Symbol"].astype(str).str.replace(r"\.T$", "", regex=True) + ".T"

        all_dfs.append(df.copy())  # ← データ整形後に追加

        # スプレッドシート更新
        worksheet.clear()
        set_with_dataframe(worksheet, df.fillna(""))

        # バックアップ作成
        new_sheet_title = f"Watchlist_{sheet_name}_{today_str}"
        try:
            delete_existing_file_by_name(drive_service, folder_id_backup, new_sheet_title)
            new_spreadsheet = gc.create(new_sheet_title, folder_id_backup)

            set_with_dataframe(new_spreadsheet.sheet1, df.fillna(""))
            print(f"✅ 完了: {new_sheet_title}")
        except Exception as e:
            print(f"❌ 作成失敗: {new_sheet_title} - {e}")

        # 🔄 各シート処理ログの記録（シートループの最後に追加）
        elapsed_sheet = time.time() - start_time_sheet  # ※ シート処理の最初で start_time_sheet = time.time() を定義しておく
        sheet_process_logs.append({
            "sheet_name": sheet_name,
            "count": len(df),
            "elapsed": elapsed_sheet,
            "failures": [row["Symbol"] for i, row in df.iterrows() if "エラー" in str(row["MultiSign"]) or "取得失敗" in str(row["Name"])]
        })

    # --- 追加処理ここから ---
    if all_dfs:
        all_df = pd.concat(all_dfs, ignore_index=True)
        # 数値変換処理を厳密化
        filtered = all_df[pd.to_numeric(all_df["TrendScore"], errors="coerce").ge(3)].copy()
        filtered["SymbolNum"] = filtered["Symbol"].apply(symbol_to_num)
        filtered = filtered.sort_values("SymbolNum", na_position='last').drop("SymbolNum", axis=1)

        new_sheet_title = f"watchlist_signal_{today_str}"
        try:
            delete_existing_file_by_name(drive_service, folder_id_main, new_sheet_title)
            new_spreadsheet = gc.create(new_sheet_title, folder_id_main)
            set_with_dataframe(new_spreadsheet.sheet1, filtered.fillna(""))
            print(f"✅ 完了: {new_sheet_title}")
        except Exception as e:
            print(f"❌ 作成失敗: {new_sheet_title} - {e}")
    else:
        print("⚠️ 有効なデータが1件もありませんでした。watchlist_signalファイルは作成されません。")
    # --- 追加処理ここまで ---

    # 全処理終了後（print("🎉 ...")の前）に追加
    print("\n🔬 デバッグ情報:")
    print(f"全シート数: {len(sheet_list)}")
    print(f"処理済みシート数: {len(all_dfs)}")
    print(f"全データ件数: {len(all_df) if all_dfs else 0}")
    print(f"フィルタ後件数: {len(filtered) if all_dfs else 0}")
    print(f"📁 保存先フォルダID（main）: {folder_id_main}")

    print("🎉 すべての処理が完了しました")


# ================================
# ✅ メイン処理関数
# ================================

def main():
    # あなたのDrive上の目的フォルダIDに差し替えてください
    FOLDER_ID_MAIN = "1dFuJfNLSJ7tw43Ac9RKAqJ0yW49cLsIe"       # ColabNotebooks/銘柄分析/Signal
    FOLDER_ID_BACKUP = "1hN6fzMeT1ZB7I0jVRc9L_8HKIqI0Gi_W"     # ColabNotebooks/銘柄分析/Signal/backup

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
        process_all_sheets(spreadsheet_name, gc, drive_service, FOLDER_ID_MAIN, FOLDER_ID_BACKUP)

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
