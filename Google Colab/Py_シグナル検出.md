# ================================
# Sec1｜セットアップ
# ================================

!pip install --upgrade gspread gspread_dataframe google-auth yfinance --quiet

import pandas as pd
import yfinance as yf
import gspread
from google.colab import auth
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from datetime import datetime, timezone, timedelta
import google.auth
from google.colab import drive

# ================================
# Sec2｜定義・関数
# ================================

SAVE_PATH = "MyDrive/ColabNotebooks/銘柄分析/signal/backup"  # 🔧 ここを変更すれば保存先のフォルダパスを変更できます（例："MyDrive/StockReports"）

def mount_drive():
    drive.mount('/content/drive')

def authenticate_services():
    auth.authenticate_user()
    creds, _ = google.auth.default()
    return creds, gspread.authorize(creds)

def get_today_str():
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d %H:%M:%S")

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

def search_and_move_file_by_name(service, file_name, folder_id):
    """ファイル名で検索して、指定フォルダに移動する"""
    query = f"name='{file_name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    files = results.get('files', [])
    if not files:
        print(f"⚠️ ファイルが見つかりません: {file_name}")
        return

    file_id = files[0]['id']
    try:
        service.files().update(
            fileId=file_id,
            addParents=folder_id,
            removeParents='root',
            fields='id, parents'
        ).execute()
        print(f"📁 再移動成功: {file_name}")
    except Exception as e:
        print(f"❌ フォルダ再移動失敗: {file_name} - {e}")

def reorder_columns(df, preferred_order):
    existing_cols = [col for col in preferred_order if col in df.columns]
    other_cols = [col for col in df.columns if col not in existing_cols]
    return df[existing_cols + other_cols]

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
    trend_score = 0.0

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
        trend_score += 1.0
    if ma5.iloc[-2] < ma25.iloc[-2] and ma5.iloc[-1] > ma25.iloc[-1] and close.iloc[-1] > ma25.iloc[-1]:
        signals.append("5MA>25MA")
        trend_score += 1.0
    if rsi.iloc[-2] < 30 and rsi.iloc[-1] > 30 and rsi.iloc[-1] > rsi.iloc[-2] + 5:
        signals.append("RSI反発")
        trend_score += 0.5
    if hist["Volume"].iloc[-1] > 1.5 * vol_ma5.iloc[-1] and hist["Volume"].iloc[-1] > hist["Volume"].iloc[-2]:
        signals.append("出来高↑")
        trend_score += 1.0
    if close.iloc[-1] > max_high.iloc[-2] * 1.01:
        signals.append("高値突破")
        trend_score += 1.0

    disparity = ((close.iloc[-1] - ma25.iloc[-1]) / ma25.iloc[-1]) * 100
    if abs(disparity) > 5:
        signals.append(f"乖離率{disparity:+.1f}%")
    if adx.iloc[-1] >= 40:
        signals.append("ADX強↑")
        trend_score += 3.0
    elif adx.iloc[-1] >= 25:
        signals.append("ADX中↑")
        trend_score += 2.0
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

    return signals, adx_last, trend, round(trend_score, 1)

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

def analyze_trend_and_score(signals, adx_value):
    """
    signals: シグナルのリスト（例: ["出来高↑", "高値突破", "乖離率+10.5%", "ADX中↑"]）
    adx_value: 現在のADX値（float）

    戻り値:
        trend_label（例："上昇トレンド"）,
        score_str（例："4.5/5.0"）,
        mark（"◯" or "✕"）
    """
    score = 0.0
    max_score = 5.0

    # ✅ 条件1: 出来高↑（+1点）
    if "出来高↑" in signals:
        score += 1.0

    # ✅ 条件2: 高値突破（+1.5点）
    if "高値突破" in signals:
        score += 1.5

    # ✅ 条件3: 乖離率 +10%以上（+1点）
    has_disparity = any(
        "乖離率" in s and float(s.replace("乖離率", "").replace("%", "").replace("+", "")) >= 10
        for s in signals
    )
    if has_disparity:
        score += 1.0

    # ✅ 条件4: ADX値に応じた加点
    if adx_value is not None:
        if adx_value >= 40:
            score += 1.5
        elif adx_value >= 25:
            score += 1.0

    # ✅ トレンド判定
    if score >= 4.0:
        trend_label = "上昇トレンド"
    elif score >= 2.5:
        trend_label = "やや上昇傾向"
    elif score >= 1.0:
        trend_label = "横ばい〜警戒"
    else:
        trend_label = "トレンド不明"

    # ✅ 表示用のスコアとマーク
    score_str = f"{round(score, 1)}/5.0"
    mark = "◯" if score >= 4.0 else "✕"

    return trend_label, score_str, mark


# ================================
# ✅ メイン処理関数
# ================================

def process_all_sheets(spreadsheet_name):
    today_str, timestamp_str = get_today_str()
    creds, gc = authenticate_services()
    spreadsheet = gc.open(spreadsheet_name)
    sheet_list = spreadsheet.worksheets()
    folder_id, drive_service = get_drive_folder_id_by_path(SAVE_PATH, creds)

    for worksheet in sheet_list:
        sheet_name = worksheet.title
        print(f"🔍 処理中: {sheet_name}")
        df = get_as_dataframe(worksheet, evaluate_formulas=True)

        if "Symbol" not in df.columns:
            print(f"⚠️ {sheet_name} にSymbol列がありません。スキップします。")
            continue

        for col in ["Name", "Time", "Price", "Trend", "TrendScore", "Sign", "MultiSign"]:
            if col not in df.columns:
                df[col] = ""
        df["Time"] = df["Time"].astype(str)

        for i, row in df.iterrows():
            raw_symbol = None  # try前に初期化
            try:
                raw_symbol = str(row["Symbol"]).strip().replace("$", "")
                code = raw_symbol.replace(".T", "").zfill(4)
                ticker = f"{code}.T"
                stock = yf.Ticker(ticker)
                hist = stock.history(period="3mo")
                if hist.empty or len(hist) < 30:
                    continue

                latest_price = round(hist["Close"].iloc[-1], 2)
                df.at[i, "Price"] = latest_price

                if not pd.notnull(row["Name"]) or row["Name"] == "":
                    name = stock.info.get("shortName", "")
                    df.at[i, "Name"] = name

                signals, adx_value, trend, trend_score = analyze_stock(hist)
                sign_str = "✅ " + ", ".join(signals) if signals else ""
                df.at[i, "Sign"] = sign_str

                comment, _ = format_signals_to_comment(
                    signals,
                    close=hist["Close"].iloc[-1],
                    ma25=hist["Close"].rolling(25).mean().iloc[-1],
                    adx_value=adx_value
                )
                df.at[i, "MultiSign"] = comment
                df.at[i, "Time"] = timestamp_str
                df.at[i, "Trend"] = trend
                df.at[i, "TrendScore"] = trend_score

            except Exception as e:
                print(f"⚠️ エラー: {raw_symbol or '不明'} - {e}")

        # 列順の並び替えと重複列のクリーンアップ
        df = reorder_columns(df, ["Symbol", "Name", "Time", "Price", "Trend", "TrendScore", "Sign", "MultiSign"])
        df = clean_dataframe_columns(df, ["Symbol", "Name", "Time", "Price", "Trend", "TrendScore", "Sign", "MultiSign"])

        worksheet.clear()
        set_with_dataframe(worksheet, df.fillna(""))

        # スプレッドシート出力
        new_sheet_title = f"Watchlist_{sheet_name}_{today_str}"
        try:
            new_spreadsheet = gc.create(new_sheet_title)
            new_spreadsheet_id = new_spreadsheet.id
            if folder_id:
                try:
                    drive_service.files().update(
                        fileId=new_spreadsheet_id,
                        addParents=folder_id,
                        removeParents='root',
                        fields='id, parents'
                    ).execute()
                except Exception:
                    search_and_move_file_by_name(drive_service, new_sheet_title, folder_id)

            new_worksheet = new_spreadsheet.get_worksheet(0)
            set_with_dataframe(new_worksheet, df.fillna(""))
            print(f"✅ 完了: {new_sheet_title} を保存しました\n")

        except Exception as e:
            print(f"❌ 作成失敗: {new_sheet_title} - {e}")

    print("🎉 すべての処理が完了しました")

# main関数の定義（エントリーポイント）
def main():
    spreadsheet_name = "watchlist"  # 🔧 対象のスプレッドシート名を入力
    mount_drive()
    process_all_sheets(spreadsheet_name)

main()