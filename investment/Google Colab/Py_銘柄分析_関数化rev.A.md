##### Memo
📘 日本株スイングトレード分析スクリプト

[仕組み]
1.Googleドライブに保存しているスプレット上に「銘柄コード」を入力
2.Google Colab上で、このスクリプトを実行すると
    「株価データ」、「テクニカル情報」などを（表＋チャート）画像として、出力
[実装機能]
    [Python_株式売買判断]
        ver1.00 ~ ver2.00まで実装
    [Py_銘柄分析_関数化rev1]
        ver1.00
        ・名称を変更→銘柄分析_関数化rev1.00に修正
        ・関数化後、HTML画像出力がうまくいっていなかったので、きちんと見直した。
        ・チャート表示やテーブル表示なども視認性を考慮し、修正した。
        ver2.00
        ・Section8,9の内容を大幅に修正
            ➡保存処理：画像をGyazoにアップロードし、その内容をCSVとHTMLで出力
            ➡実行処理：mainでの制御内容を記載
        ver3.00
        ・HTMLの構成部分を関数化して視認性をあげた。

[未実装機能]
    ・各指標（例：短期GC, MACD上昇, RSIが中立など）の組み合わせが過去にどれくらいの確率で勝てたか（＝終値が上がったか）を元に、
##### Memo_END

# ==============================
# Sec1.1｜初期Setup
# ==============================

# 🚀 ライブラリ・フォントのインストール（必要に応じてスキップ可）
FAST_MODE = False  # ✅ 初回は必ず False にしてね

if not FAST_MODE:
    print("📦 ライブラリとフォントをインストール中...")
    !apt-get -y install fonts-noto-cjk > /dev/null
    !apt-get -y install wkhtmltopdf > /dev/null
    !pip install -q imgkit mplfinance ta
    print("✅ インストール完了")
else:
    print("🚀 FAST_MODE：インストールをスキップしました")

# ✅ 必要なモジュールのインポート（セクション別）
# --- グラフ描画・フォント設定
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager
from PIL import ImageFont, Image as PILImage

# --- 時刻・日付
import time
from datetime import datetime, timedelta, timezone
JST = timezone(timedelta(hours=9))
today_str = datetime.now(JST).strftime("%Y-%m-%d")
print(f"📅 今日の日付（JST）：{today_str}")

# --- データ処理・ファイル操作
import pandas as pd
import numpy as np
import os
import re
import io
import shutil
from collections import defaultdict
from bs4 import BeautifulSoup

# --- データ取得・指標・描画
import yfinance as yf
import mplfinance as mpf
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands
from scipy.signal import argrelextrema

# --- HTML出力・画像変換
import imgkit
config = imgkit.config(wkhtmltoimage='/usr/bin/wkhtmltoimage')  # 必要に応じて
from IPython.display import display, HTML, Image

# --- Google Drive マウント
import sys
if "google.colab" in sys.modules:
    from google.colab import drive
    if not os.path.ismount("/content/drive"):
        drive.mount('/content/drive')
    else:
        print("✅ Google Drive は既にマウントされています")

# ✅ フォント設定（matplotlib + PIL）
def setup_environment():
    from matplotlib import rcParams, font_manager
    import matplotlib.pyplot as plt
    from PIL import ImageFont
    import os

    # 確認済みの日本語フォントパス
    font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

    if not os.path.exists(font_path):
        raise FileNotFoundError("❌ 日本語フォントが見つかりませんでした。")

    global jp_font, pil_font
    jp_font = font_manager.FontProperties(fname=font_path)
    pil_font = ImageFont.truetype(font_path, 24)

    # matplotlib にフォントを適用
    rcParams["font.family"] = jp_font.get_name()
    rcParams["font.sans-serif"] = [jp_font.get_name()]
    plt.rcParams["font.family"] = jp_font.get_name()

    print(f"✅ 使用フォント: {jp_font.get_name()}")

# ==============================
# Sec2.1｜Symbol取得（Googleスプレッドシート）
# ==============================
def get_symbol_list():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQZrqf2NhMcD6ebNirrxSV_ibn1FTn2Rj-jrRI27nQcSEAgkqEQfvEZYitYoB1GT65S7qIrgGhMds1i/pub?gid=0&single=true&output=csv"
    try:
        df_symbols = pd.read_csv(sheet_url, encoding="utf-8")
        df_symbols.columns = df_symbols.columns.str.strip().str.lower()
        print(f"📄 読み込んだ列: {df_symbols.columns.tolist()}")

        if "symbol" not in df_symbols.columns:
            raise ValueError("❌ 'symbol'列が見つかりません")

        symbols = df_symbols["symbol"].dropna().tolist()
        print(f"✅ シンボル取得成功：{len(symbols)}件")
        return symbols

    except Exception as e:
        print(f"❌ シートの読み込みに失敗しました: {e}")
        return []

# ================================
# Sec2.2｜銘柄データ取得
# ================================

def get_stock_data(symbol):
    print(f"📥 データ取得中: {symbol}")
    """
    yfinanceを使って株価データを取得し、DataFrameと会社名を返す。
    """
    try:
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.info
            name = info.get("shortName", symbol)
        except Exception:
            name = symbol  # info取得失敗時も fallback

        # 🔽 データ取得はここで実行
        df = ticker.history(period="18mo", interval="1d", auto_adjust=False)

        if df.empty:
            raise ValueError("取得結果が空です")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).astype(float)
        df.index.name = "Date"

        return df, name

    except Exception as e:
        print(f"❌ データ取得エラー: {symbol} - {e}")
        return None, symbol

# ================================
# Sec3.1｜テクニカル指標
# ================================

def add_technical_indicators(df):
    print("📊 テクニカル指標計算開始")
    """
    DataFrameに複数のテクニカル指標を追加して返す。
    """
    try:
      df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
      print("✅ RSI 完了")
      df["MA5"] = df["Close"].rolling(5).mean()
      df["MA25"] = df["Close"].rolling(25).mean()
      df["MA75"] = df["Close"].rolling(75).mean()
      df["MA200"] = df["Close"].rolling(200).mean()
      df["MA25_Deviation"] = (df["Close"] - df["MA25"]) / df["MA25"] * 100
      print("✅ 移動平均・乖離率 完了")

      macd = MACD(df["Close"])
      df["MACD"] = macd.macd()
      df["MACD_Signal"] = macd.macd_signal()
      df["MACD_Diff"] = macd.macd_diff()
      print("✅ MACD 完了")

      bb = BollingerBands(df["Close"])
      df["BB_High"] = bb.bollinger_hband()
      df["BB_Low"] = bb.bollinger_lband()
      df["BB_MAVG"] = bb.bollinger_mavg()
      print("✅ ボリンジャーバンド 完了")

      adx = ADXIndicator(high=df["High"], low=df["Low"], close=df["Close"])
      df["ADX"] = adx.adx()
      df["+DI"] = adx.adx_pos()
      df["-DI"] = adx.adx_neg()
      print("✅ ADX 完了")

      stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
      df["STOCH_K"] = stoch.stoch()
      df["STOCH_D"] = stoch.stoch_signal()
      print("✅ ストキャスティクス 完了")

      df["Vol_MA5"] = df["Volume"].rolling(5).mean()
      df["Vol_MA25"] = df["Volume"].rolling(25).mean()
      print("✅ 出来高移動平均 完了")

      print("📈 全テクニカル指標の計算が完了しました\n")
      return df

    except Exception as e:
      print(f"❌ テクニカル指標の計算中にエラー発生: {type(e).__name__} - {e}")
      return df  # 途中でも使えるように返しておく

# ================================
# Sec3.2｜ファンダメンタル指標取得（辞書形式）
# ================================
def add_fundamental_indicators(ticker_obj):
    print("💹 ファンダメンタル指標の取得開始")
    fund_data = {}

    try:
        info = ticker_obj.info
    except Exception as e:
        print(f"⚠️ info取得失敗: {type(e).__name__} - {e}")
        info = {}

    try:
        fast_info = ticker_obj.fast_info
    except Exception as e:
        print(f"⚠️ fast_info取得失敗: {type(e).__name__} - {e}")
        fast_info = {}

    try:
        fund_data = {
            "MarketCap": info.get("marketCap", "N/A"),
            "PER": info.get("trailingPE", "N/A"),
            "ForwardPER": info.get("forwardPE", "N/A"),
            "EPS": info.get("trailingEps", "N/A"),
            "PBR": info.get("priceToBook", "N/A"),
            "ROE": info.get("returnOnEquity", "N/A"),
            "配当利回り": info.get("dividendYield", "N/A"),
            "配当性向": info.get("payoutRatio", "N/A"),
            "売上成長率": info.get("revenueGrowth", "N/A"),
            "EPS成長率": info.get("earningsGrowth", "N/A"),
            "自己資本比率": info.get("debtToEquity", "N/A"),
            "流動比率": info.get("currentRatio", "N/A"),
            "Beta": fast_info.get("beta", "N/A"),
            "52週高値": fast_info.get("yearHigh", "N/A"),
            "52週安値": fast_info.get("yearLow", "N/A"),
        }
        print("📘 ファンダメンタルデータ取得完了\n")
    except Exception as e:
        print(f"❌ 辞書変換エラー: {type(e).__name__} - {e}")
        fund_data = {}

    return fund_data

def classify_fundamentals(fund_data):
    growth = {
        "売上成長率": fund_data.get("売上成長率", "N/A"),
        "EPS成長率": fund_data.get("EPS成長率", "N/A"),
    }
    profitability = {
        "ROE": fund_data.get("ROE", "N/A"),
        "EPS": fund_data.get("EPS", "N/A"),
        "PER": fund_data.get("PER", "N/A"),
    }
    valuation = {
        "PBR": fund_data.get("PBR", "N/A"),
        "PER": fund_data.get("PER", "N/A"),  # 重複ありでもOK
        "MarketCap": fund_data.get("MarketCap", "N/A"),
    }
    liquidity = {
        "流動比率": fund_data.get("流動比率", "N/A"),
        "自己資本比率": fund_data.get("自己資本比率", "N/A"),
    }

    return {
        "成長性": growth,
        "収益性": profitability,
        "割安性": valuation,
        "財務健全性": liquidity
    }

# ================================
# Sec4.1｜chart描画
# ================================

def generate_full_stock_chart(df_recent, symbol, name, today_str, jp_font, show_plot=True):
    import matplotlib.ticker as mticker
    from IPython.display import Image, display
    from matplotlib import pyplot as plt
    import numpy as np
    from scipy.signal import argrelextrema

    print(f"📈 チャート生成中: {symbol}")
    add_plots = []

    # === 指標系のプロット追加 ===
    add_plots += [
        mpf.make_addplot(df_recent["MA5"], panel=0, color="black", width=1.2, alpha=0.9, label="MA5"),
        mpf.make_addplot(df_recent["MA25"], panel=0, color="darkgreen", width=0.8, alpha=0.6, label="MA25"),
        mpf.make_addplot(df_recent["MA75"], panel=0, color="darkred", width=0.5, alpha=0.4, label="MA75")
    ]

    # スイングポイント（High/Low）
    price = df_recent["Close"].values
    high_idx = argrelextrema(price, np.greater, order=5)[0]
    low_idx = argrelextrema(price, np.less, order=5)[0]
    high_marker = np.full(len(df_recent), np.nan)
    low_marker = np.full(len(df_recent), np.nan)
    high_marker[high_idx] = price[high_idx]
    low_marker[low_idx] = price[low_idx]
    add_plots += [
        mpf.make_addplot(high_marker, type='scatter', markersize=100, marker='^', color='red', panel=0, label="SwingHigh"),
        mpf.make_addplot(low_marker, type='scatter', markersize=100, marker='v', color='green', panel=0, label="SwingLow")
    ]

    # 出来高（上下）
    vol_up = df_recent["Volume"].copy()
    vol_down = df_recent["Volume"].copy()
    vol_up[df_recent["Close"] < df_recent["Open"]] = 0
    vol_down[df_recent["Close"] >= df_recent["Open"]] = 0
    add_plots += [
        mpf.make_addplot(vol_up, panel=1, type='bar', color='green', alpha=0.6, label="Volume Up"),
        mpf.make_addplot(vol_down, panel=1, type='bar', color='red', alpha=0.6, label="Volume Down")
    ]

    # RSI & MACD
    add_plots += [
        mpf.make_addplot(df_recent["RSI"], panel=2, color='black', label="RSI"),
        mpf.make_addplot(df_recent["MACD"], panel=3, color='blue', label="MACD"),
        mpf.make_addplot(df_recent["MACD_Signal"], panel=3, color='red', label="Signal"),
        mpf.make_addplot(df_recent["MACD_Diff"], panel=3, type='bar', color='purple', alpha=0.5, label="Diff")
    ]

    # パネル構成と描画
    used_panels = sorted({ap.get("panel", 0) for ap in add_plots})
    panel_count = max(used_panels) + 1
    panel_ratios = [4 if i == 0 else 1 for i in range(panel_count)]
    fig, axlist = mpf.plot(
        df_recent,
        type='candle',
        style='yahoo',
        addplot=add_plots,
        volume=False,
        panel_ratios=panel_ratios,
        figsize=(14, 8),
        returnfig=True
    )

    # ✅ ラベルベースでパネル軸を判別する
    panel_labels = {
        0: ['MA5', 'MA25', 'MA75', 'SwingHigh', 'SwingLow'],
        1: ['Volume Up', 'Volume Down'],
        2: ['RSI'],
        3: ['MACD', 'Signal', 'Diff']
    }
    panel_axes = {}
    for i, ax in enumerate(axlist):
        _, labels = ax.get_legend_handles_labels()
        for panel, keywords in panel_labels.items():
            if any(label in labels for label in keywords):
                panel_axes[panel] = ax

    price_ax = panel_axes.get(0)
    volume_ax = panel_axes.get(1)
    rsi_ax = panel_axes.get(2)
    macd_ax = panel_axes.get(3)

    # ✅ 出来高パネルの調整
    if volume_ax:
        volume_ax.ticklabel_format(style='plain', axis='y')
        def vol_formatter(x, pos):
            return "" if x == 0 else f"{x / 10_000:.1f}万"
        volume_ax.yaxis.set_major_formatter(mticker.FuncFormatter(vol_formatter))
        volume_ax.tick_params(left=False)
        volume_ax.yaxis.set_label_position("right")
        volume_ax.yaxis.tick_right()
        volume_ax.set_ylabel("出来高（万株）", fontsize=9, fontproperties=jp_font)

    # ✅ RSIパネルの装飾
    if rsi_ax:
        rsi_ax.set_ylim(0, 100)
        rsi_ax.axhline(80, color='red', linestyle='--', lw=0.8, label="_nolegend_")
        rsi_ax.axhline(20, color='green', linestyle='--', lw=0.8, label="_nolegend_")
        rsi_ax.set_yticks([20, 50, 80])
        rsi_ax.set_ylabel("RSI", fontsize=9, fontproperties=jp_font)
        rsi_ax.yaxis.set_label_position("right")
        rsi_ax.yaxis.tick_right()

    # ✅ 抵抗線・支持線の描画（20日・60日）
    support_20 = df_recent["Low"].tail(20).min()
    support_60 = df_recent["Low"].tail(60).min()
    resist_20 = df_recent["High"].tail(20).max()
    resist_60 = df_recent["High"].tail(60).max()

    # 抵抗線・支持線の描画
    resist60_line = price_ax.axhline(resist_60, color='darkred', linestyle='--', linewidth=1)
    resist20_line = price_ax.axhline(resist_20, color='red', linestyle='--', linewidth=1)
    support20_line = price_ax.axhline(support_20, color='green', linestyle='--', linewidth=1)
    support60_line = price_ax.axhline(support_60, color='darkgreen', linestyle='--', linewidth=1)

    # === 抵抗線・支持線の注釈（各線の近くに表示：はみ出し防止つき） ===
    # Y軸範囲を取得（※fig.subplots_adjustの後やplot後なら取得できる）
    x_pos = len(df_recent) - 1 + 2  # ✅ 表示位置をローソク足の右側へ2単位分ズラす

    y_min, y_max = price_ax.get_ylim()
    y_range = y_max - y_min

    # 相対オフセット量（テキスト同士の上下差もつける）
    offset_up_high = y_range * 0.06   # 抵抗線.60D
    offset_up_low  = y_range * 0.03   # 抵抗線.20D
    offset_dn_high = y_range * 0.06   # 支持線.60D
    offset_dn_low  = y_range * 0.03   # 支持線.20D

    # ヘルパー関数
    def safe_y(y, offset, direction):
        new_y = y + offset if direction == "up" else y - offset
        return min(max(new_y, y_min + 5), y_max - 5)

    # 抵抗線注釈（上に配置、かつオフセット差あり）
    price_ax.text(x_pos, safe_y(resist_60, offset_up_high, "up"), f"抵抗線.60D：{resist_60:.0f}",
                  color='darkred', fontsize=11, fontproperties=jp_font, ha='left')
    price_ax.text(x_pos, safe_y(resist_20, offset_up_low, "up"), f"抵抗線.20D：{resist_20:.0f}",
                  color='red', fontsize=11, fontproperties=jp_font, ha='left')

    # 支持線注釈（下に配置、かつオフセット差あり）
    price_ax.text(x_pos, safe_y(support_60, offset_dn_high, "down"), f"支持線.60D：{support_60:.0f}",
                  color='darkgreen', fontsize=11, fontproperties=jp_font, ha='left')
    price_ax.text(x_pos, safe_y(support_20, offset_dn_low, "down"), f"支持線.20D：{support_20:.0f}",
                  color='green', fontsize=11, fontproperties=jp_font, ha='left')

    # ✅ スイング注釈の表示（価格 + 日付をマーカーの近くに）
    # Y軸の幅をもとに相対的な吹き出しオフセットを決定
    y_min, y_max = price_ax.get_ylim()
    y_range = y_max - y_min
    offset = y_range * 0.12  # 高さの12%分上下にズラす
    # SwingHigh 注釈
    for idx in high_idx:
        if 0 <= idx < len(df_recent):
            date = df_recent.index[idx].strftime("%-m/%-d")
            price = df_recent["Close"].iloc[idx]
            new_y = price + offset if price + offset < y_max else price + offset * 0.5
            price_ax.annotate(
                f"{date}\n{price:.0f}",
                xy=(idx, price),
                xytext=(idx, new_y),
                textcoords="data",
                color='white',
                fontsize=10,
                fontproperties=jp_font,
                ha='center',
                va='bottom',
                bbox=dict(boxstyle="round,pad=0.4", fc="red", ec="darkred", lw=1),
                arrowprops=dict(arrowstyle='-|>', color='darkred')
            )
    # SwingLow 注釈
    for idx in low_idx:
        if 0 <= idx < len(df_recent):
            date = df_recent.index[idx].strftime("%-m/%-d")
            price = df_recent["Close"].iloc[idx]
            new_y = price - offset if price - offset > y_min else price - offset * 0.5
            price_ax.annotate(
                f"{date}\n{price:.0f}",
                xy=(idx, price),
                xytext=(idx, new_y),
                textcoords="data",
                color='white',
                weight='bold',
                fontsize=10,
                fontproperties=jp_font,
                ha='center',
                va='top',
                bbox=dict(boxstyle="round,pad=0.3", fc="green", ec="darkgreen", lw=1),
                arrowprops=dict(arrowstyle='-|>', color='darkgreen')
            )

    # ✅ 凡例の分離表示（左＝支持/抵抗線、右＝MA/スイングなど）
    if price_ax:
        handles, labels = price_ax.get_legend_handles_labels()

        # ✅ すべて左側にまとめて表示
        price_ax.legend(
            handles=handles,
            labels=labels,
            loc="upper left",
            fontsize=8,
            frameon=True,
            fancybox=True,
            framealpha=0.8,
            borderpad=0.5,
            prop=jp_font
        )

    # タイトルなどの余白

    if price_ax:
        price_ax.set_title(f"{symbol} - {name}", fontproperties=jp_font)
        price_ax.set_xlabel("日付", fontproperties=jp_font)
        price_ax.set_xlim(-1, len(df_recent) + 5)  # ← X軸の右端に余白を設ける

    #fig.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.05)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.08)
    chart_path = f"chart_{symbol}.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight")
    #if show_plot:
        #display(Image(chart_path))
    plt.close(fig)

    print(f"✅ チャート保存完了: {chart_path}")
    return chart_path

# ================================
# Sec5.1｜HTMLテーブル生成（カテゴリ列・直近5日対応）
# ================================

def generate_summary_html(df, df_filtered, comment_map, score_dict, category_counter, name, symbol, today_str, chart_path, fundamentals):
    # ✅ テクニカルテーブルを分離関数から取得
    df_table = generate_technical_table(df, df_filtered, comment_map)

    # ✅ HTML生成
    html_table = df_table.to_html(index=False, escape=False, border=0, classes="styled-table")

    # ✅ スタイル（元のまま）
    style = """
    <style>
    .styled-table {
        border-collapse: collapse;
        width: 100%;
        font-family: monospace;
        font-size: 14px;
        table-layout: fixed; #default=auto
        word-wrap: break-word;
    }
    .styled-table th {
        background-color: #e8f4ff;
        text-align: center;
        padding: 6px;
        border: 1px solid #ccc;
    }
    .styled-table td {
        padding: 6px;
        border: 1px solid #ccc;
        text-align: center;
        white-space: pre-wrap;
    }
    .styled-table td:last-child {
        text-align: left;
    }
    .styled-table td:nth-child(1):not(:empty) {
        background-color: #f0f8ff;
        font-weight: bold;
    }
    .styled-table td.comment-cell[data-signal^="買"] {
        color: green;
    }
    .styled-table td.comment-cell[data-signal^="売"] {
        color: red;
    }
    .styled-table td.comment-cell[data-signal*="強"] {
        font-weight: bold;
    }
    </style>
    """

    # ✅ BeautifulSoupで信号ラベル付加（元のまま）
    soup = BeautifulSoup(html_table, "html.parser")
    for row in soup.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) >= 2:
            comment = cells[-1].text.strip()
            signal_match = re.match(r"^(買[強弱]?|売[強弱]?|中立)", comment)
            if signal_match:
                cells[-1]["class"] = "comment-cell"
                cells[-1]["data-signal"] = signal_match.group(1)

    # ✅ スコアバー（そのまま）
    def score_bar(score):
        filled = min(int(abs(score) + 0.5), 10)
        empty = 10 - filled
        bar = ("<span style='color:red;'>" + "■" * filled + "</span>" if score < 0 else "■" * filled) + "□" * empty
        return f"<span class='score-cell'>{score:.1f}点｜{bar}</span>"

    # ✅ スコアバー
    total_score = sum(score_dict.values())
    score_html = f"""
    <div style='text-align:center; background:#e0f0ff; padding:10px; font-weight:bold;'>
        【総合評価】スコア: {total_score:.1f} / 30点満点
    </div>
    """

    # ✅ ファンダメンタルHTML + 統合HTML生成
    fundamental_html = generate_fundamental_html_with_bars(fundamentals)
    full_html = f"""
    <html><head><meta charset='utf-8'>{style}</head><body>
    <h4>{name}（{symbol}）｜取得日: {today_str}</h4>
    {score_html}<br>{str(soup)}<br><br>{fundamental_html}
    </body></html>
    """

    display(HTML(full_html))
    return full_html, df_table

# ================================
# Sec5.2｜テクニカルHTML生成
# ================================

def generate_technical_table(df, df_filtered, comment_map):
    df_recent_week = df_filtered[-5:]
    date_labels = [d.strftime("%Y-%m-%d") for d in df_recent_week.index]

    def row(cat, label, values):
        return [cat, label] + [f"{v:.2f}" if isinstance(v, (int, float)) else v for v in values] + [""]

    table_data = []
    table_data.append(row("基本情報", "株価（終値）", df_recent_week["Close"]))
    table_data.append(row("基本情報", "出来高", df_recent_week["Volume"] / 10000))
    table_data.append(row("チャート系", "支持線(直近20日)", df["Low"].rolling(20).min().iloc[-5:]))
    table_data.append(row("チャート系", "抵抗線(直近20日)", df["High"].rolling(20).max().iloc[-5:]))
    table_data.append(row("チャート系", "5DMA", df_recent_week["MA5"]))
    table_data.append(row("チャート系", "25DMA", df_recent_week["MA25"]))
    table_data.append(row("チャート系", "75DMA", df_recent_week["MA75"]))
    table_data.append(row("チャート系", "200DMA", df_recent_week["MA200"]))
    table_data.append(row("チャート系", "25日乖離率（%）", df_recent_week["MA25_Deviation"]))
    table_data.append(row("オシレーター系", "RSI", df_recent_week["RSI"]))
    table_data.append(row("オシレーター系", "ストキャス（%K）", df_recent_week["STOCH_K"]))
    table_data.append(row("オシレーター系", "ストキャス（%D）", df_recent_week["STOCH_D"]))
    table_data.append(row("トレンド系", "MACD", df_recent_week["MACD"]))
    table_data.append(row("トレンド系", "ADX", df_recent_week["ADX"]))
    table_data.append(row("ボラティリティ系", "BB上限", df_recent_week["BB_High"]))
    table_data.append(row("ボラティリティ系", "BB中央", df_recent_week["BB_MAVG"]))
    table_data.append(row("ボラティリティ系", "BB下限", df_recent_week["BB_Low"]))

    # カテゴリの繰り返しを空欄に
    prev_cat = None
    for row_data in table_data:
        if row_data[0] == prev_cat:
            row_data[0] = ""
        else:
            prev_cat = row_data[0]

    # コメント追加
    for row_data in table_data:
        key = row_data[1]
        entry = comment_map.get(key, [])
        comment = f"{entry[0]['signal']}｜{entry[0]['detail']} {entry[0]['note']}".strip() if entry else ""
        row_data[-1] = comment

    columns = ["カテゴリ", "指標"] + date_labels + ["コメント"]
    df_table = pd.DataFrame(table_data, columns=columns)
    df_table.reset_index(drop=True, inplace=True)

    return df_table

# ================================
# Sec5.2.1｜Comment/Score処理
# ================================

# スコアルール辞書（簡略化も可能）
score_rules = {
    "RSI": {"買強": 1, "売強": -1},
    "MACD": {"買強": 1, "売強": -1},
    "ストキャス（%K）": {"買強": 1, "売強": -1},
    "ストキャス（%D）": {"買強": 1, "売強": -1},
    "ストキャス総合": {"買強": 1, "売強": -1},
    "ADX（+DI/-DI）": {"買強": 1, "売強": -1},
    "BB上限": {"売強": -1},
    "BB下限": {"買強": 1},
    "25日乖離率（%）": {"買強": 1, "売強": -1}
}

# スコア記録用辞書
valid_categories = {"technical", "chart", "fundamental"}

# ====================
# 📌 コメント登録関数
# ====================
def add_comment(comment_map, score_dict, key, signal, detail, note="", category=None):
    if category is None:
        category = "technical"

    # 信頼度を note から抽出して signal を強化
    strength = ""
    match = re.search(r"信頼度(最強|強|中|弱)", note)
    if match:
        strength = match.group(1)
        if signal == "買い":
            signal = "買強" if strength in ["最強", "強"] else "買弱"
        elif signal == "売り":
            signal = "売強" if strength in ["最強", "強"] else "売弱"

    if key not in comment_map:
        comment_map[key] = []
    comment_map[key].append({
        "signal": signal,
        "detail": detail,
        "note": note,
        "category": category
    })

    # スコア加点
    delta = score_rules.get(key, {}).get(signal, 0)
    if category in score_dict:
        score_dict[category] += delta
    else:
        print(f"⚠️ スコア加点スキップ: '{key}' → '{category}'（delta={delta}）")

def evaluate_indicators(df):
    """
    RSI・MACD・ストキャス・ADX・BBなどを評価し、コメントとスコアを返す。
    """
    comment_map = {}
    score_dict = {
        "technical": 0,
        "chart": 0,
        "fundamental": 0
    }
    category_counter = {"technical": 0, "chart": 0, "fundamental": 0}

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    vol_increased = latest["Volume"] > df["Volume"].tail(7).mean()

    # ========== RSI ==========
    rsi = latest["RSI"]
    diff = rsi - previous["RSI"]
    trend = "上昇中" if diff > 0 else "低下中"

    if rsi >= 80:
        add_comment(comment_map, score_dict, "RSI", "売り", f"買われすぎ（{trend}）", "[信頼度強]")
    elif rsi <= 20:
        add_comment(comment_map, score_dict, "RSI", "買い", f"売られすぎ（{trend}）", "[信頼度強]")
    else:
        add_comment(comment_map, score_dict, "RSI", "中立", f"RSI={rsi:.1f}（{trend}）")

    # ========== MACD ==========
    macd_diff = latest["MACD_Diff"]
    prev_diff = previous["MACD_Diff"]
    if macd_diff > 0:
        if macd_diff - prev_diff > 0:
            note = "[信頼度強]" if vol_increased else "[信頼度中]"
            add_comment(comment_map, score_dict, "MACD", "買い", "MACD上昇中", note)
        else:
            add_comment(comment_map, score_dict, "MACD", "買い", "MACDプラス圏だが減速中", "[信頼度弱]")
    else:
        if macd_diff - prev_diff < 0:
            note = "[信頼度強]" if vol_increased else "[信頼度中]"
            add_comment(comment_map, score_dict, "MACD", "売り", "MACD下降中", note)
        else:
            add_comment(comment_map, score_dict, "MACD", "売り", "MACDマイナス圏だが減速中", "[信頼度弱]")

    # ========== ストキャス ==========
    k, d = latest["STOCH_K"], latest["STOCH_D"]
    if k < 20 and k > d:
        add_comment(comment_map, score_dict, "ストキャス（%K）", "買い", "売られすぎ圏から反転", "[信頼度強]")
    elif k > 80 and k < d:
        add_comment(comment_map, score_dict, "ストキャス（%K）", "売り", "買われすぎ圏から反落", "[信頼度強]")
    else:
        add_comment(comment_map, score_dict, "ストキャス（%K）", "中立", f"%K={k:.1f}")

    if d < 20:
        add_comment(comment_map, score_dict, "ストキャス（%D）", "買い", "売られすぎ", "[信頼度強]")
    elif d > 80:
        add_comment(comment_map, score_dict, "ストキャス（%D）", "売り", "買われすぎ", "[信頼度強]")
    else:
        add_comment(comment_map, score_dict, "ストキャス（%D）", "中立", f"%D={d:.1f}")

    # ストキャス総合
    if k < 20 and k > d:
        add_comment(comment_map, score_dict, "ストキャス総合", "買い", "GC in oversold", "[信頼度強]")
    elif k > 80 and k < d:
        add_comment(comment_map, score_dict, "ストキャス総合", "売り", "DC in overbought", "[信頼度強]")
    else:
        add_comment(comment_map, score_dict, "ストキャス総合", "中立", "シグナルなし")

    # ========== ADX ==========
    adx = latest["ADX"]
    plus_di = latest["+DI"]
    minus_di = latest["-DI"]
    if adx > 25:
        if plus_di > minus_di:
            add_comment(comment_map, score_dict, "ADX（+DI/-DI）", "買い", "トレンド強＋買い優勢", "[信頼度強]")
        elif minus_di > plus_di:
            add_comment(comment_map, score_dict, "ADX（+DI/-DI）", "売り", "トレンド強＋売り優勢", "[信頼度強]")
        else:
            add_comment(comment_map, score_dict, "ADX（+DI/-DI）", "中立", "トレンドは強いが方向感なし")
    else:
        add_comment(comment_map, score_dict, "ADX（+DI/-DI）", "中立", f"ADX={adx:.1f}：方向感弱い")

    # ========== ボリンジャーバンド ==========
    close = latest["Close"]
    bb_high = latest["BB_High"]
    bb_low = latest["BB_Low"]
    bb_mid = latest["BB_MAVG"]

    if close > bb_high:
        add_comment(comment_map, score_dict, "BB上限", "売り", "バンド上抜け", "[信頼度強]")
    elif close < bb_low:
        add_comment(comment_map, score_dict, "BB下限", "買い", "バンド下抜け", "[信頼度強]")
    else:
        zone = "上寄り" if close > bb_mid else "下寄り" if close < bb_mid else "中央"
        add_comment(comment_map, score_dict, "BB中央", "中立", f"バンド内：{zone}")

    # ========== 25日乖離率 ==========
    if "MA25_Deviation" in latest:
        dev = latest["MA25_Deviation"]
        if dev > 5:
            add_comment(comment_map, score_dict, "25日乖離率（%）", "売り", "平均より+5%以上上振れ", "[信頼度強]")
        elif dev < -5:
            add_comment(comment_map, score_dict, "25日乖離率（%）", "買い", "平均より-5%以上下振れ", "[信頼度強]")
        else:
            add_comment(comment_map, score_dict, "25日乖離率（%）", "中立", f"{dev:.1f}%")

    return comment_map, score_dict, category_counter

# ================================
# Sec5.3｜ファンダメンタルHTML生成
# ================================

def score_bar(score):
    filled = min(int(round(score)), 10)
    empty = 10 - filled
    bar = "■" * filled + "□" * empty
    return f"<span style='font-family:monospace;'>{score:.1f}点｜{bar}</span>"

def score_fundamental_value(key, val):
    try:
        if val == "N/A" or val is None:
            return 0.0
        v = float(val)

        # 各指標ごとのスコア化（10点満点基準）
        if key == "PER":
            return max(0, min(10, 20 - v))  # PER 5〜15なら高得点
        elif key == "ForwardPER":
            return max(0, min(10, 20 - v))
        elif key == "PBR":
            return max(0, min(10, 5 - v))
        elif key == "ROE":
            return min(10, v * 100 / 10)  # 10%以上で満点
        elif key == "配当利回り":
            return min(10, v * 100 / 3)  # 3%以上で満点
        elif key == "配当性向":
            return max(0, min(10, 10 - abs(v * 100 - 60) / 10))  # 60%が理想
        elif key == "自己資本比率":
            return min(10, v / 10)  # 50%以上で満点
        elif key == "流動比率":
            return min(10, v / 0.3)  # 3倍以上で満点
        elif key == "売上成長率":
            return min(10, max(0, v * 100 * 2))  # 5%以上で満点
        elif key == "EPS成長率":
            return min(10, max(0, v * 100 * 2))
        else:
            return 0.0
    except:
        return 0.0

def generate_fundamental_html_with_bars(fund_dict):
    category_map = {
        "成長性": ["売上成長率", "EPS成長率"],
        "割安性": ["PER", "PBR", "ForwardPER"],
        "財務性": ["自己資本比率", "流動比率", "ROE", "Beta"],
        "配当性": ["配当利回り", "配当性向"],
        "その他": ["MarketCap", "EPS", "52週高値", "52週安値"]
    }

    html_sections = ""
    for category, keys in category_map.items():
        rows = ""
        for key in keys:
            val = fund_dict.get(key, "N/A")
            score = score_fundamental_value(key, val)
            bar_html = score_bar(score) if isinstance(score, (int, float)) else "N/A"
            rows += f"<tr><td>{key}</td><td>{bar_html}</td></tr>"

        html_sections += f"""
        <h4>📘 {category}</h4>
        <table border='1' cellpadding='6' cellspacing='0'
               style='border-collapse: collapse; font-family: monospace; width: 100%; margin-bottom: 20px;'>
            <thead style='background-color:#e0f0ff;'>
                <tr><th>指標</th><th>評価</th></tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """
    return html_sections

# ================================
# Sec5.4｜スコア関数
# ================================

def generate_score_section(score_dict):
    def score_bar(score):
        filled = min(int(abs(score) + 0.5), 10)
        empty = 10 - filled
        bar = ("<span style='color:red;'>" + "■" * filled + "</span>"
               if score < 0 else "■" * filled) + "□" * empty
        return f"<span class='score-cell'>{score:.1f}点｜{bar}</span>"

    total_score = sum(score_dict.values())

    score_html = f"""
    <div style='text-align:center; background:#e0f0ff; padding:10px; font-weight:bold;'>
        【総合評価】スコア: {total_score:.1f} / 30点満点
    </div>

    <table border='1' cellpadding='6' cellspacing='0'
          style='border-collapse: collapse; font-family: monospace; margin-top:10px; width: 100%;'>
        <thead style='background-color:#f0f0f0;'>
            <tr>
                <th>ファンダメンタル</th>
                <th>テクニカル</th>
                <th>チャート</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class='score-td'>{score_bar(score_dict['fundamental'])}</td>
                <td class='score-td'>{score_bar(score_dict['technical'])}</td>
                <td class='score-td'>{score_bar(score_dict['chart'])}</td>
            </tr>
        </tbody>
    </table>
    """
    return score_html

# 補助関数
def generate_score_section(score_dict):
    def score_bar(score):
        filled = min(int(abs(score) + 0.5), 10)
        empty = 10 - filled
        bar = ("<span style='color:red;'>" + "■" * filled + "</span>"
               if score < 0 else "■" * filled) + "□" * empty
        return f"<span class='score-cell'>{score:.1f}点｜{bar}</span>"

    total_score = sum(score_dict.values())

    score_html = f"""
    <div style='text-align:center; background:#e0f0ff; padding:10px; font-weight:bold;'>
        【総合評価】スコア: {total_score:.1f} / 30点満点
    </div>

    <table border='1' cellpadding='6' cellspacing='0'
           style='border-collapse: collapse; font-family: monospace; margin-top:10px; width: 100%;'>
        <thead style='background-color:#f0f0f0;'>
            <tr>
                <th>ファンダメンタル</th>
                <th>テクニカル</th>
                <th>チャート</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class='score-td'>{score_bar(score_dict['fundamental'])}</td>
                <td class='score-td'>{score_bar(score_dict['technical'])}</td>
                <td class='score-td'>{score_bar(score_dict['chart'])}</td>
            </tr>
        </tbody>
    </table>
    """
    return score_html

# ================================
# Sec6.1｜保存処理：関数定義・サブルーチン
# ================================

import os
import imgkit
import requests
from PIL import Image
from IPython.display import display
import csv
from pathlib import Path
import pandas as pd
import hashlib
from datetime import datetime, timedelta, timezone
import shutil
import traceback
from matplotlib import font_manager

# ✅ 日本語フォント設定
font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
jp_font = font_manager.FontProperties(fname=font_path)

# ✅ 保存先フォルダ共通設定（Drive内）
REPORT_DIR = "/content/drive/MyDrive/ColabNotebooks/銘柄分析/report/"
Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)

# ✅ Gyazoトークン
GYAZO_TOKEN = "VbP8FQFvnNREgTPDnSSNTgNaOfVwS2DZOCZDmPMclYU"

# ✅ キャッシュパス（Drive側に固定）
GYAZO_CACHE_FILE = os.path.join(REPORT_DIR, "gyazo_uploaded.csv")
CACHE_RETENTION_DAYS = 14

# ✅ Gyazoアップロード
def upload_to_gyazo(image_path, access_token):
    with open(image_path, 'rb') as f:
        files = {'imagedata': f}
        data = {'access_token': access_token}
        response = requests.post('https://upload.gyazo.com/api/upload', data=data, files=files)
        if response.status_code == 200:
            result = response.json()
            return result.get("image_url") or result.get("url")
        else:
            raise Exception(f"Gyazoアップロード失敗: {response.status_code}, {response.text}")

# ✅ HTMLハッシュ計算
def hash_html(html_str):
    return hashlib.md5(html_str.encode("utf-8")).hexdigest()

# ✅ キャッシュ初期化（初回）
def init_gyazo_cache_if_missing(path):
    if not Path(path).exists():
        print("🆕 Gyazoキャッシュファイルが存在しないため新規作成します。")
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["symbol", "date", "gyazo_url", "html_hash"])

def load_gyazo_cache(path):
    if Path(path).exists() and os.path.getsize(path) > 0:
        try:
            df = pd.read_csv(path, encoding="utf-8")
            expected_columns = {"symbol", "date", "gyazo_url", "html_hash"}
            if not expected_columns.issubset(df.columns):
                raise ValueError(f"❌ キャッシュファイルに必要なカラムが足りません: {df.columns.tolist()}")
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            cutoff = datetime.now() - timedelta(days=CACHE_RETENTION_DAYS)
            df = df[df["date"] >= cutoff].copy()
            return df
        except Exception as e:
            print(f"⚠️ キャッシュ読み込みエラー: {e}")
            return pd.DataFrame(columns=["symbol", "date", "gyazo_url", "html_hash"])
    else:
        return pd.DataFrame(columns=["symbol", "date", "gyazo_url", "html_hash"])

def is_already_uploaded_with_same_html(cache_df, symbol, today_str, html_hash):
    matched = cache_df[(cache_df["symbol"] == symbol) & (cache_df["date"] == today_str)]
    if matched.empty:
        return False
    return matched.iloc[0]["html_hash"] == html_hash

def append_to_gyazo_cache(path, symbol, today_str, url, html_hash):
    with open(path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([symbol, today_str, url, html_hash])

# ✅ HTML → PNG → 結合 → Gyazoアップロード
def save_combined_chart_and_table(chart_path, html_table, symbol, name, today_str, gyazo_token):
    try:
        temp_html_path = "/tmp/temp_table.html"
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_table)

        table_img_path = chart_path.replace(".png", "_table.png")
        imgkit.from_file(
            temp_html_path,
            table_img_path,
            options={
                "quiet": "",
                "zoom": "2.0",
                "encoding": "UTF-8",
                "width": "1400",
            }
        )

        chart_img = Image.open(chart_path)
        table_img = Image.open(table_img_path)
        width = max(chart_img.width, table_img.width)
        chart_img = chart_img.resize((width, chart_img.height))
        table_img = table_img.resize((width, table_img.height))

        combined_height = chart_img.height + table_img.height
        combined_img = Image.new("RGB", (width, combined_height), (255, 255, 255))
        combined_img.paste(chart_img, (0, 0))
        combined_img.paste(table_img, (0, chart_img.height))

        temp_output_path = f"/tmp/{symbol}_{today_str}.jpg"
        combined_img.save(temp_output_path)
        print(f"✅ 一時結合画像保存: {temp_output_path}")

        img_url = upload_to_gyazo(temp_output_path, gyazo_token)
        print(f"🌐 Gyazoアップロード成功: {img_url}")
        return img_url

    except Exception as e:
        print(f"❌ 画像結合 or Gyazoアップロードエラー: {e}")
        return None

# ✅ HTMLレポート出力
def export_to_html(results, filename):
    html_filename = Path(filename).stem + ".html"
    html_path = Path(REPORT_DIR) / html_filename  # 最初からDrive側に保存

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><style>")
        f.write("table { border-collapse: collapse; width: 100%; }")
        f.write("th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }")
        f.write("</style></head><body>")
        f.write("<h2>銘柄分析レポート</h2>")
        f.write("<table>")
        f.write("<tr><th>Symbol</th><th>Name</th><th>Time</th><th>プレビュー</th><th>リンク</th></tr>")

        for row in results:
            f.write("<tr>")
            for i, col in enumerate(row):
                if i == 3:
                    try:
                        url = col.split('"')[1]
                        f.write(f"<td><a href='{url}' target='_blank'><img src='{url}' width='200'></a></td>")
                    except:
                        f.write("<td>ERROR</td>")
                else:
                    f.write(f"<td>{col}</td>")
            f.write("</tr>")

        f.write("</table></body></html>")

    print(f"🌐 HTMLレポートもDriveに保存: {html_path}")

# ================================
# Sec6.2｜main関数（実行ブロック）
# ================================

def main():
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%Y-%m-%d_%H-%M")

    setup_environment()
    symbols = get_symbol_list()
    results = []

    init_gyazo_cache_if_missing(GYAZO_CACHE_FILE)
    cache_df = load_gyazo_cache(GYAZO_CACHE_FILE)

    for symbol in symbols:
        try:
            df, name = get_stock_data(symbol)
            if df is None:
                continue
            df = add_technical_indicators(df)
            df_recent = df.tail(60).copy()

            if len(df_recent) < 10:
                print(f"⚠️ {symbol} はデータ不足のためスキップ（{len(df_recent)}行）")
                continue

            chart_path = generate_full_stock_chart(df_recent, symbol, name, today_str, jp_font)

            # ✅ ファンダメンタル指標取得を追加（重要！）
            ticker = yf.Ticker(symbol)
            fundamentals = add_fundamental_indicators(ticker)

            comment_map, score_dict, category_counter = evaluate_indicators(df)
            full_html, _ = generate_summary_html(
                df, df_recent, comment_map, score_dict, category_counter,
                name, symbol, today_str, chart_path, fundamentals
            )

            html_hash = hash_html(full_html)

            if is_already_uploaded_with_same_html(cache_df, symbol, today_str, html_hash):
                print(f"🔁 スキップ: {symbol} は前回と同一内容")
                img_url = cache_df.loc[
                    (cache_df["symbol"] == symbol) & (cache_df["date"] == today_str),
                    "gyazo_url"
                ].values[0]
            else:
                img_url = save_combined_chart_and_table(
                    chart_path=chart_path,
                    html_table=full_html,
                    symbol=symbol,
                    name=name,
                    today_str=today_str,
                    gyazo_token=GYAZO_TOKEN
                )
                if img_url:
                    append_to_gyazo_cache(GYAZO_CACHE_FILE, symbol, today_str, img_url, html_hash)

            img_preview = f'=IMAGE("{img_url}", 1)' if img_url else "ERROR"
            img_link = f'=HYPERLINK("{img_url}", "Gyazoで開く")' if img_url else "ERROR"
            results.append([symbol, name, time_str, img_preview, img_link])

        except Exception as e:
            print(f"❌ {symbol} でエラー発生: {e}")
            traceback.print_exc()
            results.append([symbol, "ERROR", time_str, "ERROR", "ERROR"])

    output_filename = f"{today_str}_Symbol_total[{len(results)}].csv"
    csv_path = os.path.join(REPORT_DIR, output_filename)
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Symbol", "Name", "Time", "Result", "Link"])
        writer.writerows(results)

    print(f"📁 CSVをGoogle Driveに保存: {csv_path}")
    export_to_html(results, csv_path)

# ==============================
# ✅ 実行開始（ColabではこれでOK）
# ==============================
# 必要な認証はGoogle Driveへのアクセスのみ（Mount済なら不要）

# 実行
main()