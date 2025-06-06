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

font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
jp_font = font_manager.FontProperties(fname=font_path)
plt.rcParams['font.family'] = jp_font.get_name()
pil_font = ImageFont.truetype(font_path, 24)
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

        trend_signals = []
        try:
            highs_idx = argrelextrema(df_recent["High"].values, np.greater, order=5)[0]
            lows_idx = argrelextrema(df_recent["Low"].values, np.less, order=5)[0]

            if len(highs_idx) >= 2 and len(lows_idx) >= 2:
                swing_highs = df_recent.iloc[highs_idx][["High"]]
                swing_lows = df_recent.iloc[lows_idx][["Low"]]

                swing_highs["type"] = "high"
                swing_lows["type"] = "low"
                swings = pd.concat([swing_highs, swing_lows])
                swings.sort_index(inplace=True)

                for i in range(2, len(swing_highs)):
                    prev_high = swing_highs["High"].iloc[i-1]
                    curr_high = swing_highs["High"].iloc[i]
                    prev_low = swing_lows["Low"].iloc[i-1]
                    curr_low = swing_lows["Low"].iloc[i]

                    if curr_high > prev_high and curr_low > prev_low:
                        trend_signals.append(("上昇トレンド継続", swing_highs.index[i]))
                    elif curr_high < prev_high and curr_low < prev_low:
                        trend_signals.append(("下降トレンド継続", swing_lows.index[i]))
                    else:
                        trend_signals.append(("レンジor転換", swing_highs.index[i]))

        except Exception as e:
            print("❌ ダウ理論分析中にエラー:", e)
            swing_highs = pd.DataFrame()
            swing_lows = pd.DataFrame()

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
            mpf.make_addplot(df_recent["RSI"], panel=2, color="green", label="RSI")
        )
        ## Panel 3
        # ✅ MACD一式
        add_plots += [
            mpf.make_addplot(df_recent["MACD"], panel=3, color="blue", width=1.0, label="MACD"),
            mpf.make_addplot(df_recent["MACD_Signal"], panel=3, color="red", width=1.0, label="Signal"),
            mpf.make_addplot(df_recent["MACD_Diff"], panel=3, type='bar', color='purple', alpha=0.5, label="Diff")
        ]

        # Panel代入確認用
        print("📋 add_plots に含まれる panel 構成:")
        for i, ap in enumerate(add_plots):
            panel = ap.get('panel', 0)
            # labelがなくてもylabelで代替表示
            label = ap.get('ylabel') or ap.get('label') or f'plot_{i}'
            print(f"🔹 Plot {i}: panel={panel}, label='{label}'")

        ## チャート描画
        # ✅ mpf.plot() の呼び出し（volume=True は使用しない）
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

        ## Panel 0 = Price / MA
        # 注釈（極値マーカー）
        price_ax = axlist[0]
        price = df_recent["Close"].values
        high_idx = argrelextrema(price, np.greater, order=5)[0]
        low_idx = argrelextrema(price, np.less, order=5)[0]

        # 直近5日間で見た相対的に高い値＝（スイングハイ）
        for idx in high_idx:
            val = df_recent["High"].iloc[idx]
            date = df_recent.index[idx].strftime('%-m/%-d')
            price_ax.annotate(
                f"{date}\n{val:.0f}",
                xy=(df_recent.index[idx], val),
                xytext=(df_recent.index[idx], val + 50),
                arrowprops=dict(arrowstyle='->'),
                fontsize=8,
                color='darkred'
            )
        # 直近5日間で見た相対的に安い値＝（スイングロー）
        for idx in low_idx:
            val = df_recent["Low"].iloc[idx]
            date = df_recent.index[idx].strftime('%-m/%-d')
            price_ax.annotate(
                f"{date}\n{val:.0f}",
                xy=(df_recent.index[idx], val),
                xytext=(df_recent.index[idx], val - 50),
                arrowprops=dict(arrowstyle='->'),
                fontsize=8,
                color='darkgreen'
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
        # 出来高-株探風
        import matplotlib.ticker as mticker
        # ✅ 万株表示
        def format_volume_ticks(x, _):
            return f"{int(x / 10_000)}" if x >= 10_000 else "0"
        volume_ax = axlist[1]
        volume_ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_volume_ticks))
        volume_ax.set_ylabel("（万株）", fontsize=10)
        volume_ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, integer=True))
        # 最大値に応じたY軸上限調整（任意）
        max_vol = df_recent["Volume"].max()
        ymax = int((max_vol // 1_000_000 + 2) * 1_000_000)
        # 🔒 VolumeパネルのAxesを label から安全に取得
        volume_index = next(i for i, ap in enumerate(add_plots) if ap.get("label") in ["Volume Up", "Volume Down"])
        volume_ax = axlist[volume_index]

        ## Panel 2 = RSI
        # RSIのAxesを label から安全に1つだけ取得
        rsi_index = next(i for i, ap in enumerate(add_plots) if ap.get("label") == "RSI")
        rsi_ax = axlist[rsi_index]
        rsi_ax.set_ylim(0, 100)
        rsi_ax.axhline(80, color='red', linestyle='--', lw=0.8)
        rsi_ax.axhline(20, color='grenn', linestyle='--', lw=0.8)

        ## Panel 3 = MACD

        # 保存と表示
        # 各パネルに凡例（legend）を追加
        for ax in axlist:
            ax.legend(loc="upper right", fontsize=8)
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
