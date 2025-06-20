# ==============================
# 🔧 初期セットアップと依存関係
# ==============================

# 🚀 FAST_MODE = True にするとインストールをスキップできます（時短）
FAST_MODE = False  # 初回や再起動後は必ず False にしてください

if not FAST_MODE:
    print("📦 ライブラリとフォントをインストール中...")
    !apt-get -y install fonts-noto-cjk > /dev/null
    !apt-get install -y wkhtmltopdf > /dev/null
    !pip install -q imgkit mplfinance ta
    print("✅ インストール完了")
else:
    print("🚀 FAST_MODE：インストールをスキップしました")

# ==============================
# ✅ フォント設定（matplotlib + PIL）
# ==============================
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import ImageFont

# フォント読み込み
font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
jp_font = font_manager.FontProperties(fname=font_path)
pil_font = ImageFont.truetype(font_path, 24)

# matplotlib全体に適用
import matplotlib as mpl
mpl.rcParams['font.family'] = jp_font.get_name()

print(f"✅ 日本語フォント設定完了：{jp_font.get_name()}")

# ==============================
# ✅ JSTタイムゾーン + 本日の日付
# ==============================
from datetime import datetime, timedelta, timezone
JST = timezone(timedelta(hours=9))
today_str = datetime.now(JST).strftime("%Y-%m-%d")
print(f"📅 今日の日付（JST）：{today_str}")

######### 0.Condig（設定）

import imgkit
import io
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import os
import pandas as pd
import random
import re
import yfinance as yf
from datetime import datetime, timedelta, timezone
from IPython.display import Image, display
from IPython.display import display, HTML
from matplotlib import font_manager
from PIL import Image as PILImage, ImageDraw, ImageFont
from scipy.signal import argrelextrema
from ta.momentum import StochasticOscillator
from ta.trend import ADXIndicator, CCIIndicator, MACD, IchimokuIndicator
from ta.volatility import BollingerBands
from ta import momentum
from tabulate import tabulate

## 📂 Google Drive マウント
from google.colab import drive
drive.mount('/content/drive')
print("✅ Google Drive がマウントされました")

# Google Sheets（CSV）から銘柄リスト取得
import pandas as pd
# 🔗 公開された Google Sheets の CSV 出力リンク（必要に応じて変更可）
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQZrqf2NhMcD6ebNirrxSV_ibn1FTn2Rj-jrRI27nQcSEAgkqEQfvEZYitYoB1GT65S7qIrgGhMds1i/pub?gid=0&single=true&output=csv"
try:
    df_symbols = pd.read_csv(sheet_url)
    symbols = df_symbols["Symbol"].dropna().tolist()
    print(f"✅ シンボル取得成功：{len(symbols)}件")
except Exception as e:
    print(f"❌ シートの読み込みに失敗しました: {e}")
    symbols = []

## 表示フラグ
SHOW_VOLUME_MA = 1
SHOW_PRICE_MA = 1
SHOW_MA_DEVIATION = 1
SHOW_TRENDLINE = 1
SHOW_RSI = 1
SHOW_ADX = 1
SHOW_MACD = 1
SHOW_STOCH = 1
SHOW_BB = 1
SHOW_SAVE_CHART = 1

## 補助・関数群
# ユーティリティ系関数：数値をK/M/Bで省略表示
def abbreviate_number(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return str(n)

# チャート＋テーブル保存関数
"""
表（HTML）とチャート画像を結合し、JPGと必要に応じてPDFとして保存。
"""
def save_combined_chart_and_table(chart_path, html_table, output_dir, symbol, name, today_str,
                                  table_image_path="table_temp.jpg", save_pdf=False):
    """
    HTMLテーブルとチャート画像を結合し、JPG＋（オプションで）PDFとして保存する
    """

    # ✅ HTML→画像化（StylerなしHTMLを使用）
    with open("temp_table.html", "w", encoding="utf-8") as f:
        f.write(html_table)

    # ✅ wkhtmltoimageのパス取得
    import shutil
    wkhtml_path = shutil.which("wkhtmltoimage") or "/usr/bin/wkhtmltoimage"
    if not os.path.exists(wkhtml_path):
        raise EnvironmentError("❌ wkhtmltoimage が見つかりません。Colabまたは環境にインストールしてください。")

    # ✅ imgkitオプション（画像出力形式と品質）
    import imgkit
    config = imgkit.config(wkhtmltoimage=wkhtml_path)
    options = {
        'format': 'jpg',
        'encoding': "UTF-8",
        'custom-header': [('Accept-Encoding', 'gzip')],
        'quality': '85',
        'zoom': 2,
        'crop-w': 1600  # 必要に応じて横幅を調整
    }
    try:
        imgkit.from_file("temp_table.html", table_image_path, config=config, options=options)
    except Exception as e:
        raise RuntimeError(f"❌ HTMLテーブル画像化に失敗しました: {e}")

    # ✅ PILで画像読み込み（テーブル→上、チャート→下）
    from PIL import Image as PILImage
    chart_img = PILImage.open(chart_path)
    table_img = PILImage.open(table_image_path)

    # ✅ リサイズ（幅を統一）
    def resize_to_width(img, target_width):
        w, h = img.size
        if w == target_width:
            return img
        new_h = int(h * (target_width / w))
        return img.resize((target_width, new_h), PILImage.LANCZOS)

    max_width = max(chart_img.width, table_img.width)
    table_img = resize_to_width(table_img, max_width)
    chart_img = resize_to_width(chart_img, max_width)

    # ✅ 画像結合
    combined_height = table_img.height + chart_img.height
    combined_img = PILImage.new("RGB", (max_width, combined_height), "white")
    #combined_img.paste(table_img, (0, 0))
    #combined_img.paste(chart_img, (0, table_img.height))
    combined_img.paste(chart_img, (0, 0))                     # ← 先にチャート
    combined_img.paste(table_img, (0, chart_img.height))      # ← 後にテーブル

    # ✅ 保存パス準備
    save_folder = os.path.join(output_dir, f"{symbol}_{name}")
    os.makedirs(save_folder, exist_ok=True)
    base_filename = f"{symbol}_{name}_{today_str}"
    jpg_path = os.path.join(save_folder, base_filename + ".jpg")

    # ✅ JPG保存
    combined_img.save(jpg_path, optimize=True, quality=95)
    print(f"✅ JPGとして保存しました：{jpg_path}")

    # ✅ PDF保存（オプション）
    if save_pdf:
        pdf_path = os.path.join(save_folder, base_filename + ".pdf")
        combined_img.convert("RGB").save(pdf_path, "PDF", resolution=100.0)
        print(f"📄 PDFとしても保存しました：{pdf_path}")

# 信頼度と出来高を含む注釈を整形
def format_note(strength, vol_increased=None):
    note = f"[信頼度{strength}]"
    if vol_increased is not None:
        note += " 出来高増加" if vol_increased else " 出来高減少"
    return note

def is_crossed_up(cur, base, cur_prev, base_prev, epsilon=1e-3):
    return cur > base and cur_prev <= base_prev + epsilon

def abbreviate_number(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return f"{n:.0f}"

######### 1.ループ-START

for symbol in symbols:
    try:
        info = yf.Ticker(symbol).info
        name = info.get("shortName", "名称不明")
        df = yf.download(symbol, period="15mo", interval="1d", auto_adjust=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).astype(float)
        df.index.name = "Date"
        # テクニカル指標
        df["RSI"] = momentum.RSIIndicator(df["Close"], window=14).rsi()
        df["Vol_MA5"] = df["Volume"].rolling(5).mean()
        df["Vol_MA25"] = df["Volume"].rolling(25).mean()
        df["MA5"] = df["Close"].rolling(5).mean()
        df["MA25"] = df["Close"].rolling(25).mean()
        df["MA75"] = df["Close"].rolling(75).mean()
        df["MA200"] = df["Close"].rolling(200).mean()
        if SHOW_MACD:
            macd = MACD(df["Close"])
            df["MACD"] = macd.macd()
            df["MACD_Signal"] = macd.macd_signal()
            df["MACD_Diff"] = macd.macd_diff()
        if SHOW_BB:
            bb = BollingerBands(df["Close"])
            df["BB_High"] = bb.bollinger_hband()
            df["BB_Low"] = bb.bollinger_lband()
            df["BB_MAVG"] = bb.bollinger_mavg()
        if SHOW_ADX:
            from ta.trend import ADXIndicator
            adx = ADXIndicator(high=df["High"], low=df["Low"], close=df["Close"], window=14)
            df["ADX"] = adx.adx()
            df["+DI"] = adx.adx_pos()
            df["-DI"] = adx.adx_neg()
        if SHOW_STOCH:
            stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
            df["STOCH_K"] = stoch.stoch()
            df["STOCH_D"] = stoch.stoch_signal()
        if SHOW_MA_DEVIATION:
            df["MA25_Deviation"] = (df["Close"] - df["MA25"]) / df["MA25"] * 100
        df_filtered = df.dropna().copy()
        df_recent = df_filtered[-60:].copy()
        if df_recent.empty:
            print(f"⚠️ {symbol} はデータ不足でスキップ")
            continue

######### 2.チャート-START

        # 指標-移動平均
        df["MA5"] = df["Close"].rolling(window=5).mean()
        df["MA25"] = df["Close"].rolling(window=25).mean()
        df["MA75"] = df["Close"].rolling(window=75).mean()

        # 指標-RSI（簡易版）
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # 指標-MACD
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Diff"] = df["MACD"] - df["MACD_Signal"]

        # チャート対象期間（例：直近60日）
        df_recent = df.tail(60)

        # 極値インデックスを取得
        from scipy.signal import argrelextrema
        import numpy as np

        # 描画準備
        add_plots = []

        ## Panel 0
        # MA5・MA25・MA75 をすべて価格パネル（panel=0）に追加
        add_plots += [
            mpf.make_addplot(df_recent["MA5"], panel=0, color="blue", width=1.0, label="MA5"),
            mpf.make_addplot(df_recent["MA25"], panel=0, color="orange", width=1.2, label="MA25"),  # 既存のまま
            mpf.make_addplot(df_recent["MA75"], panel=0, color="purple", width=1.2, label="MA75"),
        ]
        # 極値にマーカーを表示する処理（スイングハイ／ロー）
        price = df_recent["Close"].values
        high_idx = argrelextrema(price, np.greater, order=5)[0]
        low_idx = argrelextrema(price, np.less, order=5)[0]
        high_marker = np.full(len(df_recent), np.nan)
        low_marker = np.full(len(df_recent), np.nan)
        high_marker[high_idx] = price[high_idx]
        low_marker[low_idx] = price[low_idx]
        add_plots += [
            mpf.make_addplot(high_marker, type='scatter', markersize=100, marker='^', color='red', panel=0, label="SwingHigh"),
            mpf.make_addplot(low_marker, type='scatter', markersize=100, marker='v', color='green', panel=0, label="SwingLow"),
        ]

        # ダウ理論分析ブロック
        trend_signals = []  # ここで初期化
        try:
            highs_idx = argrelextrema(df_recent["High"].values, np.greater, order=5)[0]
            lows_idx = argrelextrema(df_recent["Low"].values, np.less, order=5)[0]

            if len(highs_idx) >= 2 and len(lows_idx) >= 2:
                # 高値・安値の取得
                swing_highs = df_recent.iloc[highs_idx][["High"]].copy()
                swing_lows = df_recent.iloc[lows_idx][["Low"]].copy()
                swing_highs["type"] = "high"
                swing_lows["type"] = "low"
                swing_highs["Date"] = df_recent.index[highs_idx]
                swing_lows["Date"] = df_recent.index[lows_idx]

                # インデックスを揃える
                swing_highs.reset_index(drop=True, inplace=True)
                swing_lows.reset_index(drop=True, inplace=True)

                # 分析スタート
                loop_len = min(len(swing_highs), len(swing_lows))
                for i in range(1, loop_len):
                    prev_high = swing_highs["High"].iloc[i - 1]
                    curr_high = swing_highs["High"].iloc[i]
                    prev_low = swing_lows["Low"].iloc[i - 1]
                    curr_low = swing_lows["Low"].iloc[i]

                    if curr_high > prev_high and curr_low > prev_low:
                        trend_signals.append(("上昇トレンド継続", swing_highs["Date"].iloc[i]))
                    elif curr_high < prev_high and curr_low < prev_low:
                        trend_signals.append(("下降トレンド継続", swing_lows["Date"].iloc[i]))
                    else:
                        trend_signals.append(("レンジor転換", swing_highs["Date"].iloc[i]))
        except Exception as e:
            print("❌ ダウ理論分析中にエラー:", type(e).__name__, "-", e)
            trend_signals = []  # エラー時に空のリストに

            swing_highs = swing_highs.reset_index(drop=True)
            swing_lows = swing_lows.reset_index(drop=True)

        ## Panel 1
        # [出来高]上昇日と下落日に分けて volume データを分割
        vol_up = df_recent["Volume"].copy()
        vol_down = df_recent["Volume"].copy()
        # [出来高]フィルタ処理
        vol_up[df_recent["Close"] < df_recent["Open"]] = 0
        vol_down[df_recent["Close"] >= df_recent["Open"]] = 0
        # [出来高]add_plots に追加（2種類）
        add_plots.append(
            mpf.make_addplot(vol_up, panel=1, type='bar', color='green', alpha=0.6, label="Volume Up")
        )
        add_plots.append(
            mpf.make_addplot(vol_down, panel=1, type='bar', color='red', alpha=0.6, label="Volume Down")
        )

        ## Panel 2
        # ✅ RSI
        add_plots.append(
            mpf.make_addplot(df_recent["RSI"], panel=2, color="black", label="RSI")
        )
        ## Panel 3
        # ✅ MACD一式
        add_plots += [
            mpf.make_addplot(df_recent["MACD"], panel=3, color="blue", width=1.0, label="MACD"),
            mpf.make_addplot(df_recent["MACD_Signal"], panel=3, color="red", width=1.0, label="Signal"),
            mpf.make_addplot(df_recent["MACD_Diff"], panel=3, type='bar', color='purple', alpha=0.5, label="Diff")
        ]

        ## チャート描画

        # 日本語フォントを明示的に再設定（念のため）
        import matplotlib as mpl
        mpl.rcParams['font.family'] = jp_font.get_name()
        plt.rcParams['font.family'] = jp_font.get_name()

        # ✅ 改良版の陽線包み足検出関数
        def is_bullish_engulfing_confirmed(df, i):
            if i < 1 or i >= len(df):
                return False

            prev_open = df["Open"].iloc[i - 1]
            prev_close = df["Close"].iloc[i - 1]
            curr_open = df["Open"].iloc[i]
            curr_close = df["Close"].iloc[i]

            engulf = (
                prev_close < prev_open and
                curr_close > curr_open and
                curr_open < prev_close and
                curr_close > prev_open
            )

            rsi = df["RSI"].iloc[i]
            volume_up = df["Volume"].iloc[i]
            volume_prev = df["Volume"].iloc[i - 1]

            filter_ok = (
                rsi < 35 and
                volume_up > volume_prev * 1.2
            )

            return engulf and filter_ok

        # mpf.plot() の呼び出し（volume=True は使用しない）
        fig, axlist = mpf.plot(
            df_recent,
            type='candle',
            style='yahoo',
            addplot=add_plots,
            volume=False,  # ← 自動出来高をOFF
            panel_ratios=(4, 2, 1, 1),
            figsize=(14, 8),
            returnfig=True
        )

        # メインチャートの Axes
        price_ax = axlist[0]

        for i in range(1, len(df_recent)):
            if is_bullish_engulfing_confirmed(df_recent, i):
                x0 = df_recent.index[i - 1]
                x1 = df_recent.index[i]
                x0f = price_ax.convert_xunits(x0)
                x1f = price_ax.convert_xunits(x1)
                x_mid = (x0f + x1f) / 2

                low = min(df_recent["Low"].iloc[i - 1], df_recent["Low"].iloc[i])
                high = max(df_recent["High"].iloc[i - 1], df_recent["High"].iloc[i])
                width = x1f - x0f + 0.6

                rect = plt.Rectangle(
                    (x0f - 0.3, low - 30),
                    width,
                    high - low + 60,
                    linewidth=1.5,
                    edgecolor='blue',
                    facecolor='none',
                    zorder=5,
                    transform=price_ax.transData
                )
                price_ax.add_patch(rect)

                price_ax.annotate(
                    "陽線包み足",
                    xy=(x_mid, high + 40),
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    color='blue',
                    fontproperties=jp_font,
                    transform=price_ax.transData
                )


        # ヘッダー部
        # タイトル文字列を先に定義（忘れずに！）
        title = f"{name}（{symbol}）株価チャート（直近60日） - {today_str}"
        recent_close = df["Close"].tail(25)
        start = recent_close.iloc[0]
        end = recent_close.iloc[-1]
        rate = (end - start) / start
        # トレンド判定（記号 + ラベル）
        if rate >= 0.05:
            trend_text = "▲▲ 急上昇（+5%以上）"
            trend_color = "green"
        elif rate >= 0.02:
            trend_text = "▲ 上昇（+2%以上）"
            trend_color = "green"
        elif rate <= -0.05:
            trend_text = "▼▼ 急落（-5%以上）"
            trend_color = "red"
        elif rate <= -0.02:
            trend_text = "▼ 下降（-2%以上）"
            trend_color = "red"
        else:
            trend_text = "→ 横ばい（±2%未満）"
            trend_color = "dimgray"
        # 変化率も追加
        trend_text += f"｜変化率：{rate * 100:.2f}%"
        # タイトル：会社名＋ティッカー（強調）
        fig.text(
            0.5, 0.985,
            f"{name}（{symbol}）",
            ha='center',
            va='top',
            fontsize=18,
            fontproperties=jp_font,
            weight='bold',
            color='black'
        )
        # 下段：60日チャート情報＋日付
        fig.text(
            0.5, 0.955,
            f"株価チャート（直近60日） - {today_str}",
            ha='center',
            va='top',
            fontsize=12,
            fontproperties=jp_font,
            color='dimgray'
        )
        # 必要に応じて余白も調整
        fig.subplots_adjust(top=0.92)
        # ✅ サブタイトル文字列
        subtitle = f"対象期間：{df.index[-25].strftime('%Y/%m/%d')} ～ {df.index[-1].strftime('%Y/%m/%d')}｜傾向：{trend_text}"
        axlist[0].text(
            0.5, 1.05,
            subtitle,
            transform=axlist[0].transAxes,
            ha='center',
            va='bottom',
            fontsize=14,
            fontproperties=jp_font,
            color='dimgray'
        )
        # ✅ 余白調整
        fig.subplots_adjust(top=0.90)

        ## Panel 0 = Price / MA

        # 指示線・抵抗線（短期＝20日、中期＝60日）
        support_20 = df["Low"].tail(20).min()
        support_60 = df["Low"].tail(60).min()
        resist_20 = df["High"].tail(20).max()
        resist_60 = df["High"].tail(60).max()
        price_ax = axlist[0]
        # 線を描画（色分けも反映）
        resist60_line = price_ax.axhline(resist_60, color='darkred', linestyle='--', linewidth=1)
        resist20_line = price_ax.axhline(resist_20, color='lightcoral', linestyle='--', linewidth=1)
        support20_line = price_ax.axhline(support_20, color='lightgreen', linestyle='--', linewidth=1)
        support60_line = price_ax.axhline(support_60, color='darkgreen', linestyle='--', linewidth=1)
        # 凡例ラベル（価格を含めて表示）
        legend_left = price_ax.legend(
            handles=[
                resist60_line, resist20_line,
                support20_line, support60_line
            ],
            labels=[
                f"抵抗線.60D：{resist_60:.1f}",
                f"抵抗線.20D：{resist_20:.1f}",
                f"指示線.20D：{support_20:.1f}",
                f"指示線.60D：{support_60:.1f}",
            ],
            loc="upper left",
            fontsize=8,
            frameon=True,
            fancybox=True,
            framealpha=0.8,
            borderpad=0.5,
            prop=jp_font
        )
        price_ax.add_artist(legend_left)

        # 前後5日間における極値を検出
        price_ax = axlist[0]
        price = df_recent["Close"].values
        high_idx = argrelextrema(price, np.greater, order=5)[0]
        low_idx = argrelextrema(price, np.less, order=5)[0]
        # スイングハイ
        for idx in high_idx:
            val = df_recent["High"].iloc[idx]
            date = df_recent.index[idx].strftime('%-m/%-d')
            price_ax.annotate(
                f"{date}\n{val:.0f}",
                xy=(idx, val),
                xytext=(idx, val + 80),  # ← 上方向に少しゆとり
                ha='center',
                va='bottom',
                fontsize=8,
                fontweight='bold',
                color='white',  # ← 文字色
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='red',       # ← 背景色（赤）
                    edgecolor='darkred',   # ← 枠線
                    linewidth=1,
                    alpha=0.9
                ),
                arrowprops=dict(arrowstyle='->', color='darkred', lw=1)
            )
        # スイングロー
        for idx in low_idx:
            val = df_recent["Low"].iloc[idx]
            date = df_recent.index[idx].strftime('%-m/%-d')
            price_ax.annotate(
                f"{date}\n{val:.0f}",
                xy=(idx, val),
                xytext=(idx, val - 80),
                ha='center',
                va='top',
                fontsize=8,
                fontweight='bold',
                color='white',
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='green',
                    edgecolor='darkgreen',
                    linewidth=1,
                    alpha=0.9
                ),
                arrowprops=dict(arrowstyle='->', color='darkgreen', lw=1)
            )

        # ダウ理論：トレンド注釈
        for label, dt in trend_signals:
            price = df_recent.loc[dt, "Close"]
            idx = df_recent.index.get_loc(dt)
            axlist[0].annotate(
                label,
                xy=(idx, price),
                xytext=(idx, price + 100),
                textcoords="data",
                arrowprops=dict(arrowstyle='->', color='gray'),
                fontsize=8,
                color='black'
            )

        ## Panel 1 = Volume

        # 出来高表示の数値設定
        import matplotlib.ticker as mticker
        for ax in [axlist[2], axlist[3]]:
            # Y軸スケール調整（0非表示）
            ax.set_ylim(df_recent["Volume"].max() * 0.02, df_recent["Volume"].max() * 1.1)
            def custom_formatter(x, pos):
                return "" if x == 0 else f"{x / 10_000:.1f}万"
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(custom_formatter))
            # ✅ 左目盛り非表示、右側だけ表示
            ax.tick_params(left=False)
            ax.yaxis.set_label_position("right")
            ax.yaxis.tick_right()
            # Yラベルも右側に明示
            ax.set_ylabel("出来高（万株）", fontsize=9, fontproperties=jp_font)
        # 軸ラベルも追加（任意）
        volume_ax.set_ylabel("出来高（万株）", fontsize=9)

        ## Panel 2 = RSI
        
        # RSIの数値設定
        rsi_ax = axlist[4]
        rsi_ax.set_ylim(0, 100) # スケール調整
        # しきい値ラインやラベル追加
        rsi_ax.axhline(80, color='red', linestyle='--', lw=0.8, label="_nolegend_")
        rsi_ax.axhline(20, color='green', linestyle='--', lw=0.8, label="_nolegend_")
        # RSIパネル：目盛りの数値を明示的に設定
        rsi_ax.set_yticks([20, 50, 80])  # ←シンプルでバランス良い
        # 日本語ラベルもつけるなら以下
        # rsi_ax.set_yticklabels(["0", "低", "やや低", "中間", "やや高", "高", "100"],
        # fontproperties=jp_font)
        # 日本語ラベルの表示場所（必要に応じて）
        rsi_ax.set_ylabel("RSI", fontsize=9, fontproperties=jp_font)
        rsi_ax.yaxis.set_label_position("right")
        rsi_ax.yaxis.tick_right()
        # 凡例表示
        #rsi_ax.legend(loc="upper right", fontsize=8)

        ## Panel 3 = MACD

        # 保存と表示

        # 各描画要素に日本語フォントを強制適用
        for ax in axlist:
            for label in (ax.get_xticklabels() + ax.get_yticklabels()):
                label.set_fontproperties(jp_font)
            ax.set_title(ax.get_title(), fontproperties=jp_font)
            ax.set_xlabel(ax.get_xlabel(), fontproperties=jp_font)
            ax.set_ylabel(ax.get_ylabel(), fontproperties=jp_font)

        # 各パネルに凡例（legend）を追加
        for ax in axlist:
            handles, labels = ax.get_legend_handles_labels()
            if labels:  # 凡例に表示すべきものがあれば追加
                ax.legend(loc="upper right", fontsize=8)

        # 凡例を分離して左右に表示
        handles, labels = price_ax.get_legend_handles_labels()

        # 分類（支持線・抵抗線だけ左、それ以外は右）
        left_handles = []
        left_labels = []
        right_handles = []
        right_labels = []

        for h, l in zip(handles, labels):
            if "支持線" in l or "抵抗線" in l:
                left_handles.append(h)
                left_labels.append(l)
            else:
                right_handles.append(h)
                right_labels.append(l)

        # 左上だけの凡例（4本のラインだけを明示順に）
        legend_left = price_ax.legend(
            handles=[
                resist60_line, resist20_line,
                support20_line, support60_line
            ],
            labels=[
                "抵抗線（中期60日）", "抵抗線（短期20日）",
                "支持線（短期20日）", "支持線（中期60日）"
            ],
            loc="upper left",
            fontsize=8,
            frameon=True,
            fancybox=True,
            framealpha=1.0,  # 一旦フルにして get_frame() で制御
            borderpad=0.5,
            prop=jp_font  # ← 文字化け防止！
        )
        legend_left.set_zorder(0)                      # 🔽 一番奥へ
        legend_left.get_frame().set_alpha(0.3)         # 🔍 背景だけ薄く
        price_ax.add_artist(legend_left)

        # 右上：MA系・スイング系など
        handles, labels = price_ax.get_legend_handles_labels()
        right_handles = []
        right_labels = []

        for h, l in zip(handles, labels):
            if l not in ["抵抗線（中期60日）", "抵抗線（短期20日）", "支持線（短期20日）", "支持線（中期60日）"]:
                right_handles.append(h)
                right_labels.append(l)

        price_ax.legend(
            right_handles, right_labels,
            loc="upper right",
            fontsize=8,
            frameon=True,
            fancybox=True,
            framealpha=0.8,
            borderpad=0.5,
            prop=jp_font
        )

        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        fig.savefig("chart_output.png", dpi=150, bbox_inches="tight")
        plt.show()
        plt.close(fig)

######### 2.チャート-END

######### 3.コメント（指標判断）-START

######### 3.コメント（指標判断）-END

        # スコア評価ヘッダーとテーブルHTMLを生成する関数（30点満点）
        def generate_score_header_and_table(score_dict):
            def make_bar(score):
                filled = int(round(score))
                return "■" * filled + "□" * (10 - filled)

            cat_scores = {}
            for cat in ["chart", "technical", "fundamental"]:
                raw = score_dict.get(cat, 0)
                score = min(max(raw, 0), 10)
                cat_scores[cat] = round(score, 1)

            total_score = sum(cat_scores.values())
            eval_text = (
                "✅ 買い傾向" if total_score >= 21 else
                "⚠️ やや買い" if total_score >= 15 else
                "😐 中立" if total_score >= 10 else
                "⚠️ やや売り" if total_score >= 5 else
                "❌ 売り傾向"
            )

            html = f"""
            <div style="text-align:center; background:#e0f0ff; padding:10px; font-weight:bold;">
                【総合評価】{eval_text}（スコア: {total_score:.1f} / 30点満点）
            </div>
            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; font-family: monospace; margin-top:10px;">
                <thead style="background-color:#f0f0f0;">
                    <tr>
                        <th>カテゴリ</th>
                        <th>スコア</th>
                        <th>評価バー</th>
                    </tr>
                </thead>
                <tbody>
            """
            for name_jp, key in zip(["チャート分析", "テクニカル分析", "ファンダメンタル分析"], ["chart", "technical", "fundamental"]):
                score = cat_scores[key]
                bar = make_bar(score)
                html += f"<tr><td>{name_jp}</td><td>{score:.1f} / 10</td><td>{bar}</td></tr>"

            html += "</tbody></table>"
            return html

######### 4.テーブル-START



######### 4.テーブル-END

    except Exception as e:
        print(f"❌ エラー: {symbol} - {e}")

######### 1.ループ-END
