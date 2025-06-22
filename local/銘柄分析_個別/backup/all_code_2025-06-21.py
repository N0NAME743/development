# ==============================
# Sec｜Setup.py
# ==============================

"""
初回実行時に必要なライブラリ：
pip install -r requirements.txt
または個別に以下を実行してください：

pip install yfinance japanize-matplotlib mplfinance ta pandas matplotlib openpyxl
"""

print("📄 このファイルは実行されています:", __file__)

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ✅ グローバルフォント設定（日本語表示用）
JP_FONT = "IPAexGothic"
plt.rcParams['font.family'] = JP_FONT

# ✅ Excelファイルパス
EXCEL_PATH = "Symbols.xlsx"

# ✅ 使用可能なIPAフォント確認（任意）
for f in fm.fontManager.ttflist:
    if 'IPAex' in f.name:
        print("✅ 利用可能なIPAフォント:", f.name, f.fname)

# ==============================
# Sec｜stock_data.py
# ==============================

import pandas as pd
import yfinance as yf
from setup import EXCEL_PATH

print("📄 このファイルは実行されています:", __file__)

def get_symbols_from_excel():
    try:
        df = pd.read_excel(EXCEL_PATH)
        df.columns = df.columns.str.strip().str.lower()
        if "symbol" not in df.columns:
            raise ValueError("❌ 'symbol'列が見つかりません")
        return df["symbol"].dropna().tolist()
    except Exception as e:
        print(f"❌ Excel読み込み失敗: {e}")
        return []

def fetch_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        name = ticker.info.get("shortName", symbol)
        df = ticker.history(period="18mo", interval="1d")
        if df.empty:
            raise ValueError("データが空です")
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).copy()
        return df, name
    except Exception as e:
        print(f"❌ データ取得失敗: {symbol} - {e}")
        return None, symbol

# ==============================
# Sec｜chart_config.py
# ==============================

import pandas as pd
import mplfinance as mpf
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands
from matplotlib import rcParams
import matplotlib.pyplot as plt

print("📄 このファイルは実行されています:", __file__)

def add_indicators(df):
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA25"] = df["Close"].rolling(25).mean()
    df["MA75"] = df["Close"].rolling(75).mean()
    df["RSI"] = RSIIndicator(df["Close"]).rsi()
    macd = MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    df["MACD_diff"] = df["MACD"] - df["MACD_signal"]  # ← 追加！
    bb = BollingerBands(df["Close"])
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    adx = ADXIndicator(df["High"], df["Low"], df["Close"])
    df["ADX"] = adx.adx()
    stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
    df["STOCH_K"] = stoch.stoch()
    # ✅ 一目均衡表（雲のみ）
    df["tenkan"] = (df["High"].rolling(9).max() + df["Low"].rolling(9).min()) / 2
    df["kijun"] = (df["High"].rolling(26).max() + df["Low"].rolling(26).min()) / 2
    df["senkou1"] = ((df["tenkan"] + df["kijun"]) / 2).shift(26)
    df["senkou2"] = ((df["High"].rolling(52).max() + df["Low"].rolling(52).min()) / 2).shift(26)
    return df

def plot_chart(df, symbol, name):

    rcParams['font.family'] = ['MS Gothic', 'Meiryo', 'Arial Unicode MS']  # ✅ Windows向けフォント

    df_recent = df.tail(100).copy()

    latest = df_recent.iloc[-1]

    support_20 = df_recent["Low"].tail(20).min()
    resist_20 = df_recent["High"].tail(20).max()
    support_60 = df_recent["Low"].tail(60).min()
    resist_60 = df_recent["High"].tail(60).max()

    # ==== MACD 陽陰分岐・淡色スタイル ====

    # 事前に分岐してデータを作成
    macd_up = df_recent["MACD"].where(df_recent["MACD"].diff() >= 0)
    macd_down = df_recent["MACD"].where(df_recent["MACD"].diff() < 0)

    signal_up = df_recent["MACD_signal"].where(df_recent["MACD_signal"].diff() >= 0)
    signal_down = df_recent["MACD_signal"].where(df_recent["MACD_signal"].diff() < 0)

    # MACD関連の addplot 群（panel=3）
    macd_plots = [
        mpf.make_addplot(df_recent["MACD_diff"], panel=3, type='bar', color='plum', alpha=0.5, width=0.7),
        mpf.make_addplot(macd_up, panel=3, color='#4fa3db', width=1.5),     # MACD↑：淡青
        mpf.make_addplot(macd_down, panel=3, color='#e06060', width=1.5),   # MACD↓：淡赤
        mpf.make_addplot(signal_up, panel=3, color='#e89c33', width=1.3),   # Signal↑：淡橙
        mpf.make_addplot(signal_down, panel=3, color='#b88de2', width=1.3), # Signal↓：淡紫
    ]

    fig, axes = mpf.plot(
        df_recent,
        type='candle',
        style='yahoo',
        addplot=[
            # 🌈 移動平均線 & サポート/レジスタンス
            mpf.make_addplot(df_recent["MA5"], color="#1f77b4", width=0.7),
            mpf.make_addplot(df_recent["MA25"], color="#ff7f0e", width=0.8),
            mpf.make_addplot(df_recent["MA75"], color="#9467bd", width=0.7),
            mpf.make_addplot([support_20]*len(df_recent), color="green", linestyle="dotted"),
            mpf.make_addplot([resist_20]*len(df_recent), color="red", linestyle="dotted"),
            mpf.make_addplot([support_60]*len(df_recent), color="green", linestyle="dashdot"),
            mpf.make_addplot([resist_60]*len(df_recent), color="red", linestyle="dashdot"),

            # ⚫ RSI（パネル2）→ 黒
            mpf.make_addplot(df_recent["RSI"], panel=2, color='black'),

            # 🔵 MACDヒストグラム & 線（パネル3）
            mpf.make_addplot(df_recent["MACD_diff"], panel=3, type='bar', color='plum', alpha=0.5, width=0.7),

            mpf.make_addplot(macd_up, panel=3, color='#8cc4e8', width=1.3),     # MACD↑：淡青
            mpf.make_addplot(macd_down, panel=3, color='#f6a6a6', width=1.3),   # MACD↓：淡赤

            mpf.make_addplot(signal_up, panel=3, color='#f4c187', width=1.2),   # Signal↑：淡橙
            mpf.make_addplot(signal_down, panel=3, color='#d6b3f6', width=1.2), # Signal↓：淡紫
        ],
        title=f"{name} ({symbol}) - Stock Chart",
        ylabel="Price",
        volume=True,
        figscale=1.1,
        returnfig=True
    )

    ax_main = axes[0]
    x = range(len(df_recent))
    senkou1 = df_recent["senkou1"]
    senkou2 = df_recent["senkou2"]
    ax_main.fill_between(x, senkou1, senkou2, where=(senkou1 > senkou2), facecolor="#a8e6cf", alpha=0.3)
    ax_main.fill_between(x, senkou1, senkou2, where=(senkou1 <= senkou2), facecolor="#ff8b94", alpha=0.3)

    # ✅ 一目均衡表「ねじれ」検出（交差点）
    twist_points = df_recent[(df_recent["senkou1"] > df_recent["senkou2"]).shift(1) &
                             (df_recent["senkou1"] <= df_recent["senkou2"]) |
                             (df_recent["senkou1"] < df_recent["senkou2"]).shift(1) &
                             (df_recent["senkou1"] >= df_recent["senkou2"])]

    for idx in twist_points.index:
        x_idx = df_recent.index.get_loc(idx)
        y_val = (df_recent.loc[idx, "senkou1"] + df_recent.loc[idx, "senkou2"]) / 2
        ax_main.annotate("×", xy=(x_idx, y_val), textcoords="offset points", xytext=(0, -10),
                        ha='center', fontsize=10, color="gray")

    annotation_style = dict(
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7),
        ha='center',
        va='top',
        fontsize=9,
        fontweight='bold'
    )

    #spacing = 0.07
    #base_y = 0.95
    #base_x = 0.5
    #ax_main.text(base_x, base_y, f"05DMA: {latest['MA5']:,.1f}", transform=ax_main.transAxes, color="#1f77b4", **annotation_style)
    #ax_main.text(base_x, base_y - spacing, f"25DMA: {latest['MA25']:,.1f}", transform=ax_main.transAxes, color="#ff7f0e", **annotation_style)
    #ax_main.text(base_x, base_y - 2 * spacing, f"75DMA: {latest['MA75']:,.1f}", transform=ax_main.transAxes, color="#9467bd", **annotation_style)

    # ✅ 移動平均線ラベルを左上に横並びで表示
    spacing_x = 0.18  # ラベル間の横スペース（0.10〜0.18あたりで調整可能）
    base_x = 0.01     # 左端の基準位置（横方向）
    base_y = 0.98     # 上端の高さ位置
    ax_main.text(base_x, base_y, f"05DMA: {latest['MA5']:,.1f}", transform=ax_main.transAxes,
                color="#1f77b4", ha='left', va='top',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    ax_main.text(base_x + spacing_x, base_y, f"25DMA: {latest['MA25']:,.1f}", transform=ax_main.transAxes,
                color="#ff7f0e", ha='left', va='top',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
    ax_main.text(base_x + 2*spacing_x, base_y, f"75DMA: {latest['MA75']:,.1f}", transform=ax_main.transAxes,
                color="#9467bd", ha='left', va='top',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

    x_last_idx = len(df_recent) - 1

    ax_main.annotate(f"S20: {support_20:.1f}", xy=(x_last_idx, support_20), xytext=(10, 0), textcoords='offset points',
                     ha='left', va='center', color='green', fontsize=8, fontweight='bold',
                     bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.3'))

    ax_main.annotate(f"R20: {resist_20:.1f}", xy=(x_last_idx, resist_20), xytext=(10, 0), textcoords='offset points',
                     ha='left', va='center', color='red', fontsize=8, fontweight='bold',
                     bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.3'))

    ax_main.annotate(f"S60: {support_60:.1f}", xy=(x_last_idx, support_60), xytext=(10, 0), textcoords='offset points',
                     ha='left', va='center', color='green', fontsize=8, fontweight='bold',
                     bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.3'))

    ax_main.annotate(f"R60: {resist_60:.1f}", xy=(x_last_idx, resist_60), xytext=(10, 0), textcoords='offset points',
                     ha='left', va='center', color='red', fontsize=8, fontweight='bold',
                     bbox=dict(facecolor='white', alpha=0.6, boxstyle='round,pad=0.3'))

    # ✅ 当日の株価（終値）を注釈としてメインチャートに表示
    latest_close = df_recent["Close"].iloc[-1]

    ax_main.text(
        0.95, 0.98,  # ⬅ 右端 + 上端（X:0.99 = 右寄り、Y:0.98 = 上寄り）
        f"Price: {latest_close:.1f}",
        transform=ax_main.transAxes,
        ha='right',  # ⬅ 右寄せ
        va='top',
        fontsize=9,
        fontweight='bold',
        color='black',
        bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2')
    )

    import matplotlib.ticker as mticker  # ファイル冒頭で未インポートならここでもOK
    from matplotlib.ticker import ScalarFormatter, FuncFormatter

    # ===== 出来高パネルのカスタマイズ =====
    # ✅ 出来高パネルは axes[2]
    volume_ax = axes[2]

    # mplfinance 'yahoo' スタイルに基づくデフォルト色
    color_up = '#26a69a'   # 緑
    color_down = '#ef5350' # 赤

    volume_ax.text(
        0.01, 1.0, "Volume Up", transform=volume_ax.transAxes,
        ha='left', va='top', fontsize=9, fontweight='bold', color=color_up,
        bbox=dict(facecolor='white', edgecolor=color_up, boxstyle='round,pad=0.2', alpha=0.8)
    )
    volume_ax.text(
        0.15, 1.0, "Volume Down", transform=volume_ax.transAxes,
        ha='left', va='top', fontsize=9, fontweight='bold', color=color_down,
        bbox=dict(facecolor='white', edgecolor=color_down, boxstyle='round,pad=0.2', alpha=0.8)
    )

    def english_volume_formatter(x, pos):
        if x >= 1_000_000_000:
            return f"{x/1_000_000_000:.1f}B"
        elif x >= 1_000_000:
            return f"{x/1_000_000:.1f}M"
        elif x >= 1_000:
            return f"{x/1_000:.0f}K"
        elif x == 0:
            return ""
        else:
            return str(int(x))
    # ✅ フォーマッタを明示的に設定（指数表記を抑制）
    volume_ax.yaxis.set_major_formatter(FuncFormatter(english_volume_formatter))
    # （オプション）Y軸ラベルを明示的に指定
    volume_ax.set_ylabel("Volume")

    # ✅ 当日の出来高数量を棒グラフ上に表示
    last_index = len(df_recent) - 1
    last_volume = df_recent["Volume"].iloc[-1]

    # フォーマットは既存のformatterと同じく「英語表記（小数点なし）」
    def format_volume_label(x):
        if x >= 1_000_000_000:
            return f"{int(x / 1_000_000_000)}B"
        elif x >= 1_000_000:
            return f"{int(x / 1_000_000)}M"
        elif x >= 1_000:
            return f"{int(x / 1_000)}K"
        else:
            return str(int(x))

    # パネルのY軸上限値を取得（棒グラフより上の空間を使う！）
    ylim_top = volume_ax.get_ylim()[1]

    volume_ax.annotate(
        f"Volume: {format_volume_label(last_volume)}",
        xy=(last_index - 3, ylim_top),
        xytext=(-15, -12),  # 上端からちょっと下に（- で下に下げる）
        textcoords="offset points",
        ha='center',
        fontsize=9,
        fontweight='bold',
        color='black',
        bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2')
    )

    # ===== RSIパネルのカスタマイズ =====
    rsi_ax = axes[4]  # ← 通常 RSI は panel=2 だが、出来高含めているため+1されて3番目になる（要確認）

    # RSIの目盛り位置を固定
    rsi_ax.set_yticks([20, 50, 80])
    rsi_ax.set_ylim(0, 100)

    # 水平ラインを追加
    rsi_ax.axhline(y=20, color='green', linestyle='dotted', linewidth=1)
    rsi_ax.axhline(y=80, color='red', linestyle='dotted', linewidth=1)

    latest_rsi = df_recent["RSI"].iloc[-1]
    x_last = len(df_recent) - 1

    rsi_ax.annotate(
        f"RSI: {latest_rsi:.1f}",
        xy=(x_last - 5, latest_rsi),
        xytext=(0, -12),  # ちょっと上にずらして表示
        textcoords="offset points",
        ha='center',
        fontsize=9,
        fontweight='bold',
        color='black',
        bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.2')
    )

    # ===== MACDパネルのカスタマイズ =====
    # ✅ MACDパネルに0ラインと凡例を追加
    macd_ax = axes[6]  # 通常 panel=3 → axesの5番目

    # 0ライン
    macd_ax.axhline(y=0, color='gray', linestyle='dotted', linewidth=1)

    # 凡例（右上）
    macd_ax.legend(["Diff", "MACD↑", "MACD↓", "Signal↑", "Signal↓"], loc='upper left', fontsize=8)

    # ✅ ゴールデンクロス検出＆青丸マーカー表示
    macd_cross = (df_recent["MACD"].shift(1) < df_recent["MACD_signal"].shift(1)) & \
                (df_recent["MACD"] > df_recent["MACD_signal"])

    for idx in df_recent[macd_cross].index:
        x_pos = df_recent.index.get_loc(idx)
        y_val = df_recent.loc[idx, "MACD"]
        macd_ax.plot(x_pos, y_val, marker='o', color='green', markersize=6, zorder=5)

    import os
    from datetime import datetime

    # 📅 今日の日付（例: 2025-06-21）
    today_str = datetime.now().strftime('%Y-%m-%d')

    # 📁 出力先ディレクトリ（例: chart/2385-モンスターラボ）
    folder_name = f"output/{today_str}" #{symbol}-{name}
    os.makedirs(folder_name, exist_ok=True)  # フォルダがなければ作成

    # 🖼 保存ファイル名（例: chart_2385_2025-06-21.png）
    file_name = f"chart_{symbol}_{today_str}.png"
    save_path = os.path.join(folder_name, file_name)

    # 💾 保存
    fig.savefig(save_path)
    print(f"📈 Saved with MA, S/R lines, and Ichimoku Cloud (filled): {save_path}")
    plt.close(fig)  # ✅ メモリリーク防止

    return save_path  # ✅ ← この行を追加！

# ==============================
# Sec｜gyazo_uploader.py
# ==============================

import requests

print("📄 このファイルは実行されています:", __file__)

def upload_to_gyazo(image_path: str, access_token: str, desc: str = None) -> str:
    """
    Gyazoへ画像をアップロードしてURLを返す

    Args:
        image_path (str): 画像ファイルのパス
        access_token (str): Gyazo APIトークン
        desc (str, optional): Gyazo画像の説明文（任意）

    Returns:
        str: Gyazo画像URL（失敗時はNone）
    """
    upload_url = "https://upload.gyazo.com/api/upload"

    try:
        with open(image_path, 'rb') as image_file:
            data = {'access_token': access_token}
            if desc:
                data['desc'] = desc

            response = requests.post(
                upload_url,
                data=data,
                files={'imagedata': image_file},
                timeout=10
            )

        response.raise_for_status()

        url = response.json().get("url")
        if not url:
            print("⚠️ Gyazoアップロードは成功しましたが、URLが取得できませんでした。")
            return None

        print(f"✅ Gyazoアップロード成功: {url}")
        return url

    except requests.exceptions.Timeout:
        print("❌ タイムアウトによりGyazoアップロードに失敗しました。")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTPエラーが発生しました: {e}")
        if e.response is not None:
            print(f"  - ステータスコード: {e.response.status_code}")
            print(f"  - レスポンス内容: {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
    except Exception as e:
        print(f"❌ 予期せぬエラー: {e}")

    return None

# ==============================
# main.py｜Gyazoアップロード + JSONログ + CSV出力（統合版）
# ==============================

import os
import json
import csv
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt

from setup import JP_FONT
from stock_data import get_symbols_from_excel, fetch_stock_data
from chart_config import add_indicators, plot_chart
from gyazo_uploader import upload_to_gyazo

# ✅ フォント設定
plt.rcParams['font.family'] = JP_FONT

# ✅ Gyazoアップロードを有効にするか
ENABLE_GYAZO_UPLOAD = False  # ← False にするとアップロード処理をスキップ

# ==============================
# 補助関数群
# ==============================

def load_uploaded_hashes_json(log_path):
    if not os.path.exists(log_path):
        return set(), []
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return set(entry["hash"] for entry in data), data

def append_upload_log_json(log_path, log_data, new_entry):
    log_data.append(new_entry)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def get_file_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def write_gyazo_csv(out_folder, entries):
    out_path = os.path.join(out_folder, "gyazo_uploaded.csv")
    file_exists = os.path.exists(out_path)
    with open(out_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["date", "symbol", "name", "hash", "url"])
        if not file_exists:
            writer.writeheader()
        for entry in entries:
            writer.writerow({
                "date": entry["date"],
                "symbol": entry["symbol"],
                "name": entry["name"],
                "hash": entry["hash"],
                "url": entry.get("gyazo_url", "")
            })

# ✅ 各種パスと設定

today_str = datetime.today().strftime('%Y-%m-%d')
LOG_PATH_ALL = "result/gyazo_log.json"
LOG_PATH_DAILY = f"result/{today_str}/gyazo_log.json"

# ✅ Gyazoトークン（必要に応じて変更）
GYAZO_ACCESS_TOKEN = "YOUR_GYAZO_ACCESS_TOKEN_HERE"

# フォルダ作成
os.makedirs(os.path.dirname(LOG_PATH_ALL), exist_ok=True)
os.makedirs(os.path.dirname(LOG_PATH_DAILY), exist_ok=True)

# ==============================
# メイン処理
# ==============================

def main():
    symbols = get_symbols_from_excel()
    uploaded_hashes, log_data_all = load_uploaded_hashes_json(LOG_PATH_ALL)
    _, log_data_daily = load_uploaded_hashes_json(LOG_PATH_DAILY)
    uploaded_today = []

    print(f"✅ Excelから読み込み成功: {len(symbols)}銘柄")

    for symbol in symbols:
        print(f"▶ 処理中: {symbol}")
        df, name = fetch_stock_data(symbol)
        if df is None:
            print(f"⚠ データ取得スキップ: {symbol}")
            continue

        df = add_indicators(df)
        image_path = plot_chart(df, symbol, name)
        image_hash = get_file_md5(image_path)

        if image_hash in uploaded_hashes:
            print(f"⏭ すでにアップロード済み（同一内容）: {image_path}")
            continue

        desc = f"{symbol} {name} の株価チャート（{today_str}）"
        gyazo_url = None

        if ENABLE_GYAZO_UPLOAD:
            gyazo_url = upload_to_gyazo(image_path, GYAZO_ACCESS_TOKEN, desc=desc)

        new_entry = {
            "symbol": symbol,
            "name": name,
            "date": today_str,
            "image_path": image_path,
            "gyazo_url": gyazo_url,
            "hash": image_hash,
            "score": None,
            "comment": None
        }

        append_upload_log_json(LOG_PATH_ALL, log_data_all, new_entry)
        append_upload_log_json(LOG_PATH_DAILY, log_data_daily, new_entry)
        uploaded_today.append(new_entry)

        if ENABLE_GYAZO_UPLOAD and gyazo_url:
            print(f"\U0001F517 Gyazo URL 保存: {gyazo_url}")
        elif ENABLE_GYAZO_UPLOAD:
            print("⚠ Gyazoアップロードに失敗しました")
        else:
            print("🚫 Gyazoアップロードはスキップされました")

    out_folder = f"result/{today_str}"
    os.makedirs(out_folder, exist_ok=True)
    write_gyazo_csv(out_folder, uploaded_today)
    print(f"✅ Gyazoアップロード履歴CSVを書き出しました: {out_folder}/gyazo_uploaded.csv")

if __name__ == "__main__":
    main()
