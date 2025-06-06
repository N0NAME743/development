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

        # 初期化
        add_plots = []
        panel_id = 2  # panel=0: Price, panel=1: Volume（自動）
        rsi_ax_index = None

        # 空パネルを検出して panel_ratios を自動生成する関数
        def get_used_panels(add_plots):
            used_panels = set()
            for plot in add_plots:
                if hasattr(plot, "get") and plot.get("panel") is not None:
                    used_panels.add(plot["panel"])
                elif isinstance(plot, dict) and "panel" in plot:
                    used_panels.add(plot["panel"])
            return sorted(used_panels)

        def generate_panel_ratios(used_panels, default_main=3, default_others=1):
            ratios = []
            for i in sorted(used_panels):
                if i == 0:
                    ratios.append(default_main)
                else:
                    ratios.append(default_others)
            return ratios

        df_recent["MA5"] = df_recent["Close"].rolling(window=5).mean()
        df_recent["MA25"] = df_recent["Close"].rolling(window=25).mean()
        df_recent["MA75"] = df_recent["Close"].rolling(window=75).mean()

        # ピボットポイント（株価にマーカー追加）
        price = df_recent["Close"].values
        high_idx = argrelextrema(price, np.greater, order=5)[0]
        low_idx = argrelextrema(price, np.less, order=5)[0]
        high_marker = np.full(len(df_recent), np.nan)
        low_marker = np.full(len(df_recent), np.nan)
        high_marker[high_idx] = price[high_idx]
        low_marker[low_idx] = price[low_idx]
        add_plots += [
            mpf.make_addplot(high_marker, type='scatter', markersize=100, marker='^', color='red', panel=0),
            mpf.make_addplot(low_marker, type='scatter', markersize=100, marker='v', color='green', panel=0),
        ]

        # 最終日のX座標（ローソク足の末尾）
        x_pos = len(df_recent) - 1

        # ボリンジャーバンドの設定
        #if SHOW_BB:
        #    add_plots += [
        #        mpf.make_addplot(df_recent["BB_MAVG"], panel=0, color="blue", linestyle='dotted', width=1, label="BB_MAVG"),
        #        mpf.make_addplot(df_recent["BB_High"], panel=0, color="gray", linestyle='dashed', width=1, label="BB_High"),
        #        mpf.make_addplot(df_recent["BB_Low"], panel=0, color="gray", linestyle='dashed', width=1, label="BB_Low")
        #    ]

        # RSI
        if SHOW_RSI:
            rsi_panel_id = panel_id
            add_plots.append(
                mpf.make_addplot(df_recent["RSI"], panel=rsi_panel_id, color="black", width=1.5, ylabel="RSI")
            )
            panel_id += 1

        # MACD
        if SHOW_MACD:
            macd_panel = panel_id
            buy_signal = (df_recent["MACD"].shift(1) < df_recent["MACD_Signal"].shift(1)) & (df_recent["MACD"] > df_recent["MACD_Signal"])
            sell_signal = (df_recent["MACD"].shift(1) > df_recent["MACD_Signal"].shift(1)) & (df_recent["MACD"] < df_recent["MACD_Signal"])
            vol_ma5 = df_recent["Volume"].rolling(5).mean()
            buy_filter = (df_recent["MACD"] > 0) & (df_recent["MACD_Diff"] > 0) & (df_recent["RSI"] < 70) & (df_recent["Volume"] > vol_ma5)
            sell_filter = (df_recent["MACD"] < 0) & (df_recent["MACD_Diff"] < 0) & (df_recent["RSI"] > 30) & (df_recent["Volume"] > vol_ma5)
            macd_cross_buy = df_recent["MACD"].where(buy_signal & buy_filter)
            macd_cross_sell = df_recent["MACD"].where(sell_signal & sell_filter)

            add_plots += [
                mpf.make_addplot(df_recent["MACD"], panel=macd_panel, color="green", width=1.2, ylabel="MACD"),
                mpf.make_addplot(df_recent["MACD_Signal"], panel=macd_panel, color="red", width=1.0),
                mpf.make_addplot(df_recent["MACD_Diff"], panel=macd_panel, type='bar', color="purple", alpha=0.6)
            ]
            if not macd_cross_buy.dropna().empty:
                add_plots.append(mpf.make_addplot(macd_cross_buy, panel=macd_panel, type='scatter', marker='o', markersize=80, color='green'))
            if not macd_cross_sell.dropna().empty:
                add_plots.append(mpf.make_addplot(macd_cross_sell, panel=macd_panel, type='scatter', marker='o', markersize=80, color='red'))

            panel_id += 1

        # 使用されたパネル番号から正しい比率を生成
        used_panels = get_used_panels(add_plots)
        used_panels.append(1)  # 出来高用の panel=1 を手動追加（volume=True のため）
        used_panels = sorted(set(used_panels))
        panel_ratios = generate_panel_ratios(used_panels, default_main=3, default_others=1)
        print(f"[DEBUG] panel_ratios = {panel_ratios} | used_panels = {used_panels}")

        ## チャート描画
        fig, axlist = mpf.plot(
            df_recent,
            type="candle",
            style="yahoo",
            volume=True,
            addplot=add_plots,
            scale_padding={'left': 0.25, 'right': 0.75},  # 余白を最小限に
            panel_ratios=panel_ratios,
            figsize=(14, 8),
            returnfig=True
        )

        # ✅ MAラインの最終値を定義（描画前でも後でもOK）
        ma5 = df_recent["MA5"].iloc[-1]
        ma25 = df_recent["MA25"].iloc[-1]
        ma75 = df_recent["MA75"].iloc[-1]

        # 注釈表示（y方向に少し下げて表示）
        price_ax = axlist[0]
        price_ax.text(x_pos + 1, ma5 - 50, f"MA5: {ma5:.0f}", color="blue", fontsize=8)
        price_ax.text(x_pos + 1, ma25 - 50, f"MA25: {ma25:.0f}", color="orange", fontsize=8)
        price_ax.text(x_pos + 1, ma75 - 50, f"MA75: {ma75:.0f}", color="purple", fontsize=8)

        # 📌 事前設定：注釈のスタイル
        annotation_configs = {
            "High": {"offset": 30, "color": "darkred"},
            "Low": {"offset": -30, "color": "darkgreen"},
            "Pivot": {"offset": 50, "color": "gray", "fill": "yellow"},
        }

        # 📌 極値ポイントの検出
        extrema_points = {
            "High": argrelextrema(df_recent["High"].values, np.greater, order=5)[0],
            "Low": argrelextrema(df_recent["Low"].values, np.less, order=5)[0],
            "Pivot": argrelextrema(df_recent["Close"].values, np.greater, order=5)[0],
        }

        # ✅ チャート描画（mplfinanceなどで axlist[0] を得たあと）

        # 🔽 Y軸に余白を追加（方法1）
        ymin, ymax = axlist[0].get_ylim()
        margin = (ymax - ymin) * 0.1  # 上下に10%の余白
        axlist[0].set_ylim(ymin - margin, ymax + margin)

        # ✅ 注釈描画（方法2：注釈が枠外に出ないよう制限付き）
        ymax_limit = axlist[0].get_ylim()[1] * 0.95  # Y軸上限の95%までに制限

        for label_type, indices in extrema_points.items():
            cfg = annotation_configs[label_type]
            for i, idx in enumerate(indices):
                price = (
                    df_recent["High"].iloc[idx] if label_type == "High"
                    else df_recent["Low"].iloc[idx] if label_type == "Low"
                    else df_recent["Close"].iloc[idx]
                )
                dynamic_offset = cfg["offset"] + (10 if i % 2 == 0 else -10)
                y_annot = min(price + dynamic_offset, ymax_limit)  # 枠外に出ないよう調整

                if not np.isnan(price):
                    date_label = df_recent.index[idx].strftime('%-m/%-d')
                    axlist[0].annotate(
                        f"{date_label} {price:.0f}",
                        xy=(idx, price),
                        xytext=(idx, y_annot),
                        textcoords="data",
                        arrowprops=dict(arrowstyle='->', lw=1, color=cfg["color"]),
                        fontsize=9,
                        color=cfg["color"],
                        bbox=dict(boxstyle="round", fc=cfg.get("fill", "white"), ec=cfg["color"], alpha=0.85)
                    )

        # メインタイトル文字列を定義
        title = f"{name}（{symbol}）株価チャート（直近60日） - {today_str}"
        # 描画後の axlist[0] にタイトルを設定
        axlist[0].set_title(
            title,
            fontproperties=jp_font,
            fontsize=15,
            pad=20,
        )
        # メインチャートの上にサブタイトルを表示（左寄せや中央にできる）
        # トレンド判定（ここでは方法1を使用）
        if df["MA25"].iloc[-1] < df["MA25"].iloc[0]:
            trend_text = "下降トレンド継続中"
        else:
            trend_text = "上昇トレンド継続中"
        # サブタイトル生成
        subtitle = f"対象期間：{df.index[0].strftime('%Y/%m/%d')} ～ {df.index[-1].strftime('%Y/%m/%d')}｜傾向：{trend_text}"
        # 描画処理
        axlist[0].text(
            0.5, 1.07,
            subtitle,
            transform=axlist[0].transAxes,
            ha='center',
            va='top',
            fontsize=12,
            fontproperties=jp_font,
            color='dimgray'
        )
        fig.subplots_adjust(left=0.05, right=0.95)
        fig.savefig("chart_output.png", dpi=150, bbox_inches="tight")

        # サポート・レジスタンスライン（外側に順番指定で表示）
        price_ax = axlist[0]
        sr_windows = [20, 60]
        support_colors = ["#1f77b4", "#17becf"]
        resistance_colors = ["#d62728", "#ff7f0e"]

        # 値を一時保存
        support_lines = {}
        resist_lines = {}

        for idx, window in enumerate(sr_windows):
            if len(df_recent) >= window:
                support = df_recent["Low"].rolling(window).min().iloc[-1]
                resist = df_recent["High"].rolling(window).max().iloc[-1]

                # 線の描画
                price_ax.axhline(support, color=support_colors[idx % 2], linestyle='--', linewidth=1.2, alpha=0.8)
                price_ax.axhline(resist, color=resistance_colors[idx % 2], linestyle='--', linewidth=1.2, alpha=0.8)

                # 値を辞書に保存
                support_lines[window] = support
                resist_lines[window] = resist

        # ✅ 表示順に注釈を配置
        label_y_positions = [0.95, 0.88, 0.81, 0.74]  # Y位置（上から下に）
        if 60 in resist_lines and 20 in resist_lines and 20 in support_lines and 60 in support_lines:
          price_ax.text(0.01, label_y_positions[0], f"Resistance(60d): {resist_lines[60]:.2f}",
                        transform=price_ax.transAxes, ha='left', va='center', fontsize=8, color=resistance_colors[1])
          price_ax.text(0.01, label_y_positions[1], f"Resistance(20d): {resist_lines[20]:.2f}",
                        transform=price_ax.transAxes, ha='left', va='center', fontsize=8, color=resistance_colors[0])
          price_ax.text(0.01, label_y_positions[2], f"Support(20d): {support_lines[20]:.2f}",
                        transform=price_ax.transAxes, ha='left', va='center', fontsize=8, color=support_colors[0])
          price_ax.text(0.01, label_y_positions[3], f"Support(60d): {support_lines[60]:.2f}",
                        transform=price_ax.transAxes, ha='left', va='center', fontsize=8, color=support_colors[1])

        # 凡例表示（ラベル付きの要素があるときのみ）
        if any(line.get_label() and not line.get_label().startswith("_") for line in price_ax.lines):
            price_ax.legend(loc='upper left', fontsize='small')

        # RSI表示設定
        if SHOW_RSI:
          target_rsi_ax = next((ax for ax in axlist if ax.get_ylabel() == "RSI"), None)
          if target_rsi_ax:
              target_rsi_ax.set_ylim(0, 100)
              target_rsi_ax.set_yticks([20, 40, 60, 80])
              target_rsi_ax.axhline(80, color='red', linestyle='--', linewidth=1)
              target_rsi_ax.axhline(20, color='blue', linestyle='--', linewidth=1)

        # レイアウトと保存
        chart_path = f"{symbol}_{name}_{today_str}.png"
        if SHOW_SAVE_CHART:
            try:
                fig.tight_layout()
                fig.savefig(chart_path, dpi=150)
                plt.close(fig)
            except Exception as e:
                print(f"[警告] チャート保存に失敗しました: {e}")
            if not os.path.exists(chart_path):
                raise FileNotFoundError(f"チャート画像の保存に失敗しました: {chart_path}")

######### 2.チャート-END

######### 3.コメント（指標判断）-START

        comment_map = {}  # 空の辞書として初期化

        valid_categories = {"technical", "chart", "fundamental"}

        indicator_category_map = {
            "支持線(直近20日)": "technical",
            "支持線(直近60日)": "technical",
            "抵抗線(直近20日)": "technical",
            "抵抗線(直近60日)": "technical",
            "5DMA": "technical",
            "25DMA": "technical",
            "75DMA": "technical",
            "200DMA": "technical",
            "25日乖離率（%）": "technical",
            "RSI": "technical",
            "MACD": "technical",
            "ADX（+DI/-DI）": "technical",
            "ストキャス（%K）": "technical",
            "ストキャス（%D）": "technical",
            "ストキャス総合": "technical",

            # チャート系（chart）
            "BB上限": "chart",
            "BB下限": "chart",
            "BB中央": "chart",

            # ファンダメンタル（将来追加予定）
            #"PER": "fundamental",
            #"PBR": "fundamental",
            #"EPS": "fundamental",
            }

        # ✅ マッピング追加（推奨）
        indicator_category_map.update({
            "株価（終値）": "technical",
            "出来高": "technical",
        })

        # ✅ 自動でカテゴリを付けるように関数を再定義
        def add_comment(comment_map, key, signal, detail, note="", category=None):
            if category is None:
                category = indicator_category_map.get(key, "other")  # 自動でカテゴリを補完
            # ✅ カテゴリ検証（警告出すだけ）
            if category not in valid_categories:
                print(f"⚠️ 未定義カテゴリ：{key} → '{category}'")
            if key not in comment_map:
                comment_map[key] = []
            comment_map[key].append({
                "signal": signal,
                "detail": detail,
                "note": note,
                "category": category
            })

        # ✅ スコアルール
        score_rules = {
            # 📉 サポート・レジスタンス
            "支持線(直近20日)": {"買強": 2, "買弱": 1, "売強": -2, "売弱": -1},  # 支持線反発・割れ
            "抵抗線(直近20日)": {"売強": -2, "売弱": -1, "買強": 2, "買弱": 1},  # 抵抗線突破・反落
            # 📈 移動平均線
            "5DMA": {"買強": 3, "買弱": 1, "売強": -3, "売弱": -1},    # トレンドの初動確認
            "25DMA": {"買強": 2, "買弱": 1, "売強": -2, "売弱": -1},
            "75DMA": {"買強": 2, "買弱": 1, "売強": -2, "売弱": -1},
            # 🔄 乖離（平均線とのズレ）
            "短期乖離": {"買強": 1, "売強": -1},             # 5日平均線からの離れすぎ
            "25日乖離率（%）": {"買強": 1, "売強": -1},      # 25日平均線との±5%以上の乖離
            # 📊 オシレーター系
            "RSI": {"買強": 1, "売強": -1},                 # RSI30以下なら買い
            "ストキャス（%K）": {"買強": 1, "売強": -1},
            "ストキャス（%D）": {"買強": 1, "売強": -1},
            "ストキャス総合": {"買強": 1, "売強": -1},       # GCで買い、DCで売り
            "MACD": {"買強": 1, "売強": -1},                # GCで買い、DCで売り
            # 🆕 その他
            "ADX（+DI/-DI）": {"買強": 1, "売強": -1},
            "BB上限": {"売強": -1},
            "BB下限": {"買強": 1},                          # BB下限で反発 → 買い
        }

        # ✅ スコア格納先（カテゴリ分け）
        score_dict = {
            "technical": 0,
            "chart": 0,
            "fundamental": 0
        }

        # ✅ スコアバー生成（10段階）
        def score_bar(normalized_score):
            filled = int(round(normalized_score))  # 5.7 → 6個
            empty = 10 - filled
            return "■" * filled + "□" * empty

        # ✅ 総合評価コメント生成（scoreベースに対応）
        def generate_detailed_summary_block(score, technical_score=0.0, chart_score=0.0, fundamental_score=0.0, highlights=None):
            lines = []

            # 総合評価の判定（scoreベース）
            if score >= 7:
                head = "✅ 総合評価：買い傾向"
            elif score >= 4:
                head = "⚠️ 総合評価：やや買い"
            elif score >= 1:
                head = "😐 総合評価：中立"
            elif score >= -2:
                head = "⚠️ 総合評価：やや売り"
            else:
                head = "❌ 総合評価：売り傾向"

            normalized_score = normalize_technical_score(score)
            lines.append(f"{head}（スコア: {score:.1f} / 正規化: {normalized_score:.1f}）")

            # カテゴリ別スコアバー（チャート／テクニカル／ファンダ）
            categories = [
                ("チャート分析", chart_score),
                ("テクニカル分析", technical_score),
                ("ファンダメンタル分析", fundamental_score)
            ]
            for name, value in categories:
                bar = score_bar(value)
                lines.append(f"｜{name:<12}：{bar}（{value:.1f} / 10）")

            # コメント要点
            lines.append("｜要点：")
            if highlights:
                for h in highlights:
                    lines.append(f"　・{h}")
            else:
                lines.append("　（コメント準備中）")

            return "\n".join(lines)

        # スコアが最大20点に近づいている場合の調整
        def normalize_technical_score(raw_score, max_score=20.0):
            return min(round((raw_score / max_score) * 10, 1), 10.0)

        # ✅ カテゴリ自動付与とスコア加点付きの add_comment
        def add_comment(comment_map, key, signal, detail, note="", category=None):
            # 自動カテゴリ補完
            if category is None:
                category = indicator_category_map.get(key, "other")

            # 信頼度の抽出（オプション）
            strength = ""
            if "信頼度" in note:
                import re
                match = re.search(r"信頼度(最強|強|中|弱)", note)
                if match:
                    strength = match.group(1)

            # 信号の変換
            if signal == "買い":
                signal = "買強" if strength in ["強", "最強"] else "買弱"
            elif signal == "売り":
                signal = "売強" if strength in ["強", "最強"] else "売弱"

            # ✅ コメントをリストで格納（文字列ではなく！）
            if key not in comment_map or not isinstance(comment_map[key], list):
                comment_map[key] = []

            comment_map[key].append({
                "signal": signal,
                "detail": detail,
                "note": note,
                "category": category
            })

            # ✅ スコア加点（categoryが不明ならスキップ）
            delta = score_rules.get(key, {}).get(signal, 0)
            if category in score_dict:
                score_dict[category] += delta
            else:
                print(f"⚠️ スコア加点スキップ: '{key}' → '{category}'（delta={delta}）")

        # 定義
        df_recent_week = df.tail(7) # df_recent_week の定義
        latest = df.iloc[-1]        # 最新・前日データの定義
        previous = df.iloc[-2]

        # Commnet：株価終値出来高
        diff = latest["Close"] - previous["Close"]
        add_comment(comment_map, "株価（終値）", "中立", f"終値={latest['Close']:.2f}（前日比{diff:+.2f}）")

        # Commnet：出来高
        vol_latest = latest["Volume"]
        vol_avg = df_recent_week["Volume"].mean()
        vol_increased = vol_latest > vol_avg
        diff = vol_latest - vol_avg
        pct = round((diff / vol_avg) * 100, 1)
        add_comment(comment_map, "出来高", "中立", f"7日平均={vol_avg:,.0f}（差分={diff:+,.0f} / {pct:+.1f}%）")

        # Commnet：複数期間対応のサポート・レジスタンス判定
        close_price = latest["Close"]
        for window in [20, 60]:
            support_price = df["Low"].rolling(window).min().iloc[-1]
            resist_price = df["High"].rolling(window).max().iloc[-1]
            close_price = latest["Close"]
            # --- 支持線 判定 ---
            diff_support = close_price - support_price
            pct_support = (diff_support / support_price) * 100
            diff_str = f"（{diff_support:+.2f}円 / {pct_support:+.2f}%）"
            if close_price < support_price:
                add_comment(comment_map, f"支持線(直近{window}日)", "売り", f"支持線を下抜け{diff_str}", "[信頼度強]")
            elif abs(pct_support) <= 3:
                strength = "強" if abs(pct_support) <= 2 else "弱"
                note = format_note(strength, vol_increased)
                add_comment(comment_map, f"支持線(直近{window}日)", "買い", f"支持線から反発の兆し{diff_str}", note)
            else:
                add_comment(comment_map, f"支持線(直近{window}日)", "中立", f"支持線から乖離{diff_str}")
            # --- 抵抗線 判定 ---
            diff_resist = close_price - resist_price
            pct_resist = (diff_resist / resist_price) * 100
            diff_str = f"（{diff_resist:+.2f}円 / {pct_resist:+.2f}%）"
            if close_price > resist_price:
                add_comment(comment_map, f"抵抗線(直近{window}日)", "買い", f"抵抗線を突破{diff_str}", "[信頼度強]")
            elif abs(pct_resist) <= 3:
                strength = "強" if abs(pct_resist) <= 2 else "弱"
                note = format_note(strength, vol_increased)
                add_comment(comment_map, f"抵抗線(直近{window}日)", "売り", f"抵抗線に接近中{diff_str}", note)
            else:
                add_comment(comment_map, f"抵抗線(直近{window}日)", "中立", f"抵抗線との乖離{diff_str}")

        # Commnet：移動平均線
        # ✅ MAクロス：GC／DC（5DMA・25DMA・75DMA・200DMAをペアに）
        ma_pairs = [
            ("5DMA", "25DMA", latest["MA5"], latest["MA25"], previous["MA5"], previous["MA25"], "短期"),
            ("25DMA", "75DMA", latest["MA25"], latest["MA75"], previous["MA25"], previous["MA75"], "中期"),
            ("75DMA", "200DMA", latest["MA75"], latest["MA200"], previous["MA75"], previous["MA200"], "長期"),
        ]
        for key, base_key, cur, base, cur_prev, base_prev, label in ma_pairs:
            crossed_up = cur > base and cur_prev <= base_prev
            crossed_down = cur < base and cur_prev >= base_prev
            slope_cur = cur - cur_prev
            slope_base = base - base_prev
            slope_ok = slope_cur > 0 and slope_base > 0
            diff = cur - base
            diff_str = f"{label}クロス｜差={diff:+.2f}円"

            strength = "弱"  # デフォルト

            if crossed_up:
                if slope_ok and vol_increased:
                    strength = "最強"
                elif slope_ok:
                    strength = "強"
                elif vol_increased:
                    strength = "中"
                note = format_note(strength, vol_increased)
                add_comment(comment_map, key, "買い", f"{label}GC（{diff_str}）", note)
            elif crossed_down:
                if slope_cur < 0 and slope_base < 0 and vol_increased:
                    strength = "最強"
                elif vol_increased:
                    strength = "強"
                note = format_note(strength, vol_increased)
                add_comment(comment_map, key, "売り", f"{label}DC（{diff_str}）", note)
            else:
                add_comment(comment_map, key, "中立", f"明確なクロスなし（{diff_str}）")

        # クロスが発生していたら add_comment() のみでスコア反映も完結
        if crossed_up:
            if slope_ok and vol_increased:
                strength = {"弱": "中", "中": "強", "強": "最強"}[strength]
            elif vol_increased:
                strength = {"弱": "中", "中": "強", "強": "強"}[strength]
            note = format_note(strength, vol_increased)
            add_comment(comment_map, key, "買い", f"{label}GC（{diff_str}）", note)
        elif crossed_down:
            if slope_cur < 0 and slope_base < 0 and vol_increased:
                strength = {"弱": "中", "中": "強", "強": "最強"}[strength]
            elif vol_increased:
                strength = {"弱": "中", "中": "強", "強": "強"}[strength]
            note = format_note(strength, vol_increased)
            add_comment(comment_map, key, "売り", f"{label}DC（{diff_str}）", note)
        else:
            add_comment(comment_map, key, "中立", f"明確なクロスなし（{diff_str}）")

        # Commnet：25日線乖離
            dev = latest["MA25_Deviation"]
            if dev > 5:
                add_comment(
                    comment_map,
                    "25日乖離率（%）",
                    "売り",
                    "平均より大きく上振れ（過熱感あり）",
                    "[信頼度強]"
                )
            elif dev < -5:
                add_comment(
                    comment_map,
                    "25日乖離率（%）",
                    "買い",
                    "平均より大きく下振れ（割安感あり）",
                    "[信頼度強]"
                )
            else:
                add_comment(
                    comment_map,
                    "25日乖離率（%）",
                    "中立",
                    "平均付近で安定"
                )

        # Commnet：RSI
        val, prev_val = latest["RSI"], previous["RSI"]
        diff = val - prev_val
        trend = "上昇中" if diff > 0 else "低下中"
        if val >= 82:
            strength = "強"
            note = format_note(strength, vol_increased)
            add_comment(comment_map, "RSI", "売り", f"買われすぎ（{trend} / 過熱度：{strength}）", note)
        elif val >= 80:
            strength = "中"
            note = format_note(strength, vol_increased)
            add_comment(comment_map, "RSI", "売り", f"買われすぎ（{trend} / 過熱度：{strength}）", note)
        elif val < 20:
            strength = "強" if val <= 18 else "中" if val <= 19 else "弱"
            note = format_note(strength, vol_increased)
            add_comment(comment_map, "RSI", "買い", f"売られすぎ（{trend} / 割安度：{strength}）", note)
        else:
            add_comment(comment_map, "RSI", "中立", f"明確なシグナルなし（{trend} / 前日比{diff:+.2f}）")

        # Commnet：ストキャス
        # ストキャス（%K）
        k, d = latest["STOCH_K"], latest["STOCH_D"]
        if k < 20 and k > d:
            note = "[信頼度強]"
            add_comment(comment_map, "ストキャス（%K）", "買い", "売られすぎ圏から反転の兆し", note)
        elif k > 80 and k < d:
            note = "[信頼度強]"
            add_comment(comment_map, "ストキャス（%K）", "売り", "買われすぎ圏から反落の兆し", note)
        else:
            zone = "売られすぎ圏" if k < 20 else "買われすぎ圏" if k > 80 else "中立圏"
            crossover = "ゴールデンクロス（上抜け）" if k > d else "デッドクロス（下抜け）" if k < d else "一致"
            add_comment(
                comment_map,
                "ストキャス（%K）",
                "中立",
                f"%K={k:.2f}｜{zone}（{crossover}）"
            )
        # ストキャス（%D）
        d_val, prev_d_val = latest["STOCH_D"], previous["STOCH_D"]
        diff = d_val - prev_d_val
        trend = "上昇中" if diff > 0 else "低下中"
        if d_val > 80:
            note = "[信頼度強]"
            add_comment(comment_map, "ストキャス（%D）", "売り", f"買われすぎ圏に滞在（{trend}）", note)
        elif d_val < 20:
            note = "[信頼度強]"
            add_comment(comment_map, "ストキャス（%D）", "買い", f"売られすぎ圏に滞在（{trend}）", note)
        else:
            zone = "買われすぎ圏" if d_val > 80 else "売られすぎ圏" if d_val < 20 else "中立圏"
            add_comment(comment_map, "ストキャス（%D）", "中立", f"%D={d_val:.2f}｜{zone}（{trend}）")
        # ストキャス総合（%Kと%Dの関係）
        k, d = latest["STOCH_K"], latest["STOCH_D"]
        if k < 20 and k > d:
            note = "[信頼度強]"
            add_comment(comment_map, "ストキャス総合", "買い", "売られすぎ圏でGC発生", note)
        elif k > 80 and k < d:
            note = "[信頼度強]"
            add_comment(comment_map, "ストキャス総合", "売り", "買われすぎ圏でDC発生", note)
        elif k > d and k < 50:
            add_comment(comment_map, "ストキャス総合", "中立", "中立〜買い寄り｜下位圏で上昇中")
        elif k < d and k > 50:
            add_comment(comment_map, "ストキャス総合", "中立", "中立〜売り寄り｜上位圏で下落中")
        else:
            add_comment(comment_map, "ストキャス総合", "中立", "明確なシグナルなし")

        # Commnet：MACD
        val, prev_val = latest["MACD_Diff"], previous["MACD_Diff"]
        diff = val - prev_val
        if val > 0:
            if diff > 0:
                note = "[信頼度強]"
                add_comment(comment_map, "MACD", "買い", "MACD上昇中（勢い強）", note)
            else:
                note = "[信頼度弱]"
                add_comment(comment_map, "MACD", "買い", "MACDプラス圏だが減速中（慎重に）", note)
        else:
            if diff < 0:
                note = "[信頼度強]"
                add_comment(comment_map, "MACD", "売り", "MACD下降中（勢い強）", note)
            else:
                note = "[信頼度弱]"
                add_comment(comment_map, "MACD", "売り", "MACDマイナス圏だが減速中（様子見）", note)

        # Commnet：ADX
        plus_di = latest["+DI"]
        minus_di = latest["-DI"]
        adx_val = latest["ADX"]
        trend_note = ""
        signal = "中立"
        note = ""
        category = "technical"
        # トレンド方向の判定条件
        if adx_val >= 20:
            if plus_di > minus_di:
                signal = "買い"
                trend_note = "買いトレンド（+DI > -DI）"
                note = "[信頼度強]" if adx_val > 25 else "[信頼度中]"
            elif minus_di > plus_di:
                signal = "売り"
                trend_note = "売りトレンド（-DI > +DI）"
                note = "[信頼度強]" if adx_val > 25 else "[信頼度中]"
            else:
                trend_note = "方向感なし（DI交差）"
        else:
            trend_note = "トレンド弱く方向性なし"
            signal = "中立"

        add_comment(
            comment_map,
            "ADX（+DI/-DI）",
            signal,
            f"ADX={adx_val:.1f}｜+DI={plus_di:.1f}, -DI={minus_di:.1f}｜{trend_note}",
            note,
            category=category
        )
        try:
            di_pos = latest["+DI"]
            di_neg = latest["-DI"]
            if not np.isnan(di_pos) and not np.isnan(di_neg):
                if di_pos > di_neg:
                    add_comment(comment_map, "ADX（+DI/-DI）", "買い", f"+DI優勢（+DI={di_pos:.2f} > -DI={di_neg:.2f}）", "[信頼度強]")
                elif di_neg > di_pos:
                    add_comment(comment_map, "ADX（+DI/-DI）", "売り", f"-DI優勢（-DI={di_neg:.2f} > +DI={di_pos:.2f}）", "[信頼度強]")
                else:
                    add_comment(comment_map, "ADX（+DI/-DI）", "中立", f"+DIと-DIが拮抗（{di_pos:.2f} ≒ {di_neg:.2f}）")
        except KeyError as e:
            print(f"❌ エラー: {symbol} - '{e.args[0]}' が見つかりません")

        # Comment：BB
        diff_from_mid = latest["Close"] - latest["BB_MAVG"]
        band_width = latest["BB_High"] - latest["BB_Low"]
        deviation = (latest["Close"] - latest["BB_Low"]) / band_width * 100
        if latest["Close"] > latest["BB_High"]:
            note = "[信頼度強]"
            add_comment(
                comment_map,
                "BB上限",
                "売り",
                f"{latest['Close']:.2f}円（終値） > BB上限={latest['BB_High']:.2f}円｜バンドを上抜け（買われすぎ）🚨",
                note
            )
        elif latest["Close"] < latest["BB_Low"]:
            note = "[信頼度強]"
            add_comment(
                comment_map,
                "BB下限",
                "買い",
                f"{latest['Close']:.2f}円（終値） < BB下限={latest['BB_Low']:.2f}円｜バンドを下抜け（売られすぎ）📉",
                note
            )
        else:
            zone = (
                "上寄り（やや割高）" if deviation > 66 else
                "下寄り（やや割安）" if deviation < 33 else
                "中央付近（安定圏）"
            )
            add_comment(
                comment_map,
                "BB中央",
                "中立",
                f"{latest['Close']:.2f}円（終値）はバンド内の{zone}｜中心乖離={diff_from_mid:+.2f}円"
            )

        # ✅ 各判定処理（add_commentの中で自動的に加点される）
        total_score = sum(score_dict.values())
        normalized_score = normalize_technical_score(score_dict["technical"])

        # ✅ チェック1：未定義カテゴリがないか確認（← ここに入れる！）
        for key, comments in comment_map.items():
            for comment in comments:
                cat = comment.get("category", "none")
                if cat not in valid_categories:
                    print(f"⚠️ 未定義カテゴリ: {key} → '{cat}'")

        # ✅ チェック2（任意）：カテゴリごとの件数を集計したい場合
        from collections import Counter
        category_counter = Counter([c["category"] for v in comment_map.values() for c in v])
        print("✅ カテゴリ別コメント数：")
        for k, v in category_counter.items():
            print(f"　- {k}: {v}件")

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

        # 表データの作成
        df_recent_week = df_filtered[-7:]
        date_labels = [d.strftime("%-m/%-d") for d in df_recent_week.index]
        divider = lambda name: [f"── {name} ──"] + ["" for _ in df_recent_week.index]
        table_data = []
        table_data.append(["株価（終値）"] + [f"{v:.2f}" for v in df_recent_week["Close"]])
        table_data.append(["出来高"] + [abbreviate_number(v) for v in df_recent_week["Volume"]])
        # 20日間のサポート／レジスタンス（当日までの値を使う）
        support_20d = df["Low"].rolling(20).min().iloc[-7:]
        resist_20d = df["High"].rolling(20).max().iloc[-7:]
        # テーブルに追加（株価の直下）
        table_data.append(["支持線(直近20日)"] + [f"{v:.2f}" for v in support_20d])
        table_data.append(["抵抗線(直近20日)"] + [f"{v:.2f}" for v in resist_20d])
        table_data.append(divider("移動平均系"))
        if SHOW_PRICE_MA:
            table_data.append(["5DMA"] + [f"{v:.2f}" for v in df_recent_week["MA5"]])
            table_data.append(["25DMA"] + [f"{v:.2f}" for v in df_recent_week["MA25"]])
            table_data.append(["75DMA"] + [f"{v:.2f}" for v in df_recent_week["MA75"]])
            table_data.append(["200DMA"] + [f"{v:.2f}" for v in df_recent_week["MA200"]])
        if SHOW_MA_DEVIATION:
            table_data.append(["25日乖離率（%）"] + [f"{v:.2f}" for v in df_recent_week["MA25_Deviation"]])
        table_data.append(divider("オシレーター系"))
        if SHOW_RSI:
            table_data.append(["RSI"] + [f"{v:.2f}" for v in df_recent_week["RSI"]])
        if SHOW_STOCH:
            table_data.append(["ストキャス（%K）"] + [f"{v:.2f}" for v in df_recent_week["STOCH_K"]])
            table_data.append(["ストキャス（%D）"] + [f"{v:.2f}" for v in df_recent_week["STOCH_D"]])
        table_data.append(divider("トレンド系"))
        if SHOW_MACD:
            table_data.append(["MACD"] + [f"{v:.2f}" for v in df_recent_week["MACD"]])
        if SHOW_ADX:
            table_data.append(["ADX"] + [f"{v:.2f}" for v in df_recent_week["ADX"]])
        table_data.append(divider("ボラティリティ系"))
        if SHOW_BB:
            table_data.append(["BB上限"] + [f"{v:.2f}" for v in df_recent_week["BB_High"]])
            table_data.append(["BB中央"] + [f"{v:.2f}" for v in df_recent_week["BB_MAVG"]])
            table_data.append(["BB下限"] + [f"{v:.2f}" for v in df_recent_week["BB_Low"]])

        # DataFrameに変換
        df_table = pd.DataFrame(table_data, columns=["指標"] + date_labels)

        def extract_comment_text(key):
            entries = comment_map.get(key, [])
            if not entries:
                return ""
            entry = entries[0]  # 最初のコメントだけ使う（必要に応じて複数対応も可）
            return f"{entry['signal']}｜{entry['detail']} {entry['note']}".strip()

        comment_list = []
        for row in table_data:
            key = row[0]
            if key.startswith("──"):
                comment_list.append("")
            else:
                comment_list.append(extract_comment_text(key))

        df_table["コメント"] = comment_list

        # コメント列を追加_修正版（アイコンなしでコメントをそのまま使う）
        def get_style_by_comment(comment):
            if not comment:
                return ""

            comment = str(comment).strip()

            # シグナルを抽出（買強／買弱／売強／売弱／中立）に対応
            signal_match = re.match(r"^(買[強弱]|売[強弱]|中立)[|｜]", comment)
            if not signal_match:
                return ""

            signal = signal_match.group(1)

            # 中立は無色
            if signal == "中立":
                return ""

            # 色と太字の設定
            color = "green" if "買" in signal else "red"
            weight = "bold" if "強" in signal else "normal"

            return f"color: {color}; font-weight: {weight}"

        # コメントスタイルを行に適用する関数
        def apply_row_style(row):
            comment = row["コメント"]
            return [get_style_by_comment(comment) if col != "指標" else "" for col in row.index]

        # 総合評価テーブル（タイトル＋スコアバー表）
        score_summary_html = generate_score_header_and_table(score_dict)

        # スタイル付きHTML出力
        styled_df = df_table.style.apply(apply_row_style, axis=1)
        html_table = styled_df.to_html(render_links=False, escape=False)

        # CSS（コメント列を左寄せ）
        style = """
        <style>
        table {
          border-collapse: collapse;
          width: auto;
        }
        th, td {
          padding: 4px;
          border: 1px solid gainsboro;
          text-align: center;
        }
        td:last-child {
          text-align: left !important;
        }
        </style>
        """
        legend_html = """
        <p style="font-weight: bold; margin-top: 10px;">
        📘 凡例（指標分類）：
        <span style="background:#f0f8ff; padding: 2px 6px;">移動平均系</span>
        <span style="background:#fffaf0; padding: 2px 6px;">オシレーター系</span>
        <span style="background:#f5f5f5; padding: 2px 6px;">トレンド系</span>
        <span style="background:#f0fff0; padding: 2px 6px;">ボラティリティ系</span>
        </p>
        """

        # ✅ 最終HTML構成
        full_html = f"""
        <html>
        <head>
        <meta charset="utf-8">
        {style}
        </head>
        <body>
        <h4>{name}（{symbol}）｜取得日: {today_str}</h4>
        {score_summary_html}
        <br>{legend_html}{html_table}
        </body>
        </html>
        """
        # 表示
        display(Image(chart_path))  # ① チャート画像
        display(HTML(full_html))    # ② 総合評価コメント

        save_combined_chart_and_table(
            chart_path=chart_path,
            html_table=full_html,
            output_dir="/content/drive/MyDrive/ColabNotebooks/銘柄分析",
            symbol=symbol,
            name=name,
            today_str=today_str,
            save_pdf=False
        )

######### 4.テーブル-END

    except Exception as e:
        print(f"❌ エラー: {symbol} - {e}")

######### 1.ループ-END
