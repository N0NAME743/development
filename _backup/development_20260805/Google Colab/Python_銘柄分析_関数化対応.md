# ==============================
# Sec1｜初期セットアップ（Colab対応）
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
    !apt-get -y install fonts-noto-cjk
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

    # --- Google Drive マウント
    from google.colab import drive
    drive.mount('/content/drive')
    print("✅ Google Drive がマウントされました")

    # --- データ処理・ファイル操作
    import pandas as pd
    import numpy as np
    import os
    import re
    import io
    import shutil
    from collections import defaultdict

    # --- データ取得・指標・描画
    import yfinance as yf
    import mplfinance as mpf
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.trend import MACD, ADXIndicator
    from ta.volatility import BollingerBands
    from scipy.signal import argrelextrema

    # --- HTML出力・画像変換
    import imgkit
    from IPython.display import display, HTML, Image

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

        print(f"✅ 使用フォント: {jp_font.get_name()}")

# ==============================
# Sec2｜シンボル取得（Googleスプレッドシート）
# ==============================
def get_symbol_list():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQZrqf2NhMcD6ebNirrxSV_ibn1FTn2Rj-jrRI27nQcSEAgkqEQfvEZYitYoB1GT65S7qIrgGhMds1i/pub?gid=0&single=true&output=csv"
    try:
        df_symbols = pd.read_csv(sheet_url)
        symbols = df_symbols["Symbol"].dropna().tolist()
        print(f"✅ シンボル取得成功：{len(symbols)}件")
        return symbols
    except Exception as e:
        print(f"❌ シートの読み込みに失敗しました: {e}")
        return []

# ================================
# Sec3｜株価データ取得
# ================================
def get_stock_data(symbol):
    print(f"📥 データ取得中: {symbol}")
    """
    yfinanceを使って株価データを取得し、DataFrameと会社名を返す。
    """
    try:
        info = yf.Ticker(symbol).info
        name = info.get("shortName", "名称不明")

        df = yf.download(symbol, period="15mo", interval="1d", auto_adjust=False)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"]).astype(float)
        df.index.name = "Date"
        return df, name

    except Exception as e:
        print(f"❌ データ取得エラー: {symbol} - {e}")
        return None, None

# ================================
# Sec4｜テクニカル指標付加
# ================================
def add_technical_indicators(df):
    print("📊 テクニカル指標計算中...")
    """
    DataFrameに複数のテクニカル指標を追加して返す。
    """
    df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA25"] = df["Close"].rolling(25).mean()
    df["MA75"] = df["Close"].rolling(75).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["MA25_Deviation"] = (df["Close"] - df["MA25"]) / df["MA25"] * 100

    macd = MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Diff"] = macd.macd_diff()

    bb = BollingerBands(df["Close"])
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    df["BB_MAVG"] = bb.bollinger_mavg()

    adx = ADXIndicator(high=df["High"], low=df["Low"], close=df["Close"])
    df["ADX"] = adx.adx()
    df["+DI"] = adx.adx_pos()
    df["-DI"] = adx.adx_neg()

    stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()

    df["Vol_MA5"] = df["Volume"].rolling(5).mean()
    df["Vol_MA25"] = df["Volume"].rolling(25).mean()

    return df

# ================================
# Sec5｜チャート描画
# ================================
def plot_stock_chart(df_recent, symbol, name, today_str, jp_font, show_plot=True):
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

    # === 抵抗線・支持線の注釈（各線のすぐ上に表示） ===
    x_pos =  0 # 右端＝len(df_recent) - 1
    # 抵抗線
    price_ax.text(x_pos, resist_60 + 30, f"抵抗線.60D：{resist_60:.0f}",
                  color='darkred', fontsize=11, fontproperties=jp_font, ha='left')
    price_ax.text(x_pos, resist_20 + 30, f"抵抗線.20D：{resist_20:.0f}",
                  color='red', fontsize=11, fontproperties=jp_font, ha='left')
    # 指示線
    price_ax.text(x_pos, support_20 - 30, f"指示線.20D：{support_20:.0f}",
                  color='green', fontsize=11, fontproperties=jp_font, ha='left')
    price_ax.text(x_pos, support_60 - 30, f"指示線.60D：{support_60:.0f}",
                  color='darkgreen', fontsize=11, fontproperties=jp_font, ha='left')

    # ✅ スイング注釈の表示（価格 + 日付をマーカーの近くに）
    for idx in high_idx:
        if 0 <= idx < len(df_recent):
            date = df_recent.index[idx].strftime("%-m/%-d")
            price = df_recent["Close"].iloc[idx]
            price_ax.annotate(f"{date}\n{price:.0f}",
                xy=(idx, price),
                xytext=(idx, price + 80),
                textcoords="data",
                color='white',
                fontsize=10,
                fontproperties=jp_font,
                ha='center',
                va='bottom',
                bbox=dict(boxstyle="round,pad=0.4", fc="red", ec="darkred", lw=1),
                arrowprops=dict(arrowstyle='-|>', color='darkred'))
    for idx in low_idx:
        if 0 <= idx < len(df_recent):
            date = df_recent.index[idx].strftime("%-m/%-d")
            price = df_recent["Close"].iloc[idx]
            price_ax.annotate(f"{date}\n{price:.0f}",
                xy=(idx, price),
                xytext=(idx, price - 80),
                textcoords="data",
                color='white',
                weight='bold',
                fontsize=10,
                fontproperties=jp_font,
                ha='center',
                va='top',
                bbox=dict(boxstyle="round,pad=0.3", fc="green", ec="darkgreen", lw=1),
                arrowprops=dict(arrowstyle='-|>', color='darkgreen'))

    # ✅ 凡例の分離表示（左＝支持/抵抗線、右＝MA/スイングなど）
    if price_ax:
        handles, labels = price_ax.get_legend_handles_labels()
        left_handles, left_labels, right_handles, right_labels = [], [], [], []
        for h, l in zip(handles, labels):
            if '支持線' in l or '抵抗線' in l:
                left_handles.append(h)
                left_labels.append(l)
            else:
                right_handles.append(h)
                right_labels.append(l)

        # 左側（支持線/抵抗線）
        legend_left = price_ax.legend(
            handles=left_handles,
            labels=left_labels,
            loc="upper left",
            fontsize=8,
            frameon=True,
            fancybox=True,
            framealpha=0.3,
            borderpad=0.5,
            prop=jp_font
        )
        #price_ax.add_artist(legend_left)  # 表示/非表示

        # 右側（MAやスイング）
        price_ax.legend(
            handles=right_handles,
            labels=right_labels,
            loc="upper right",
            fontsize=8,
            frameon=True,
            fancybox=True,
            framealpha=0.8,
            borderpad=0.5,
            prop=jp_font
        )
        price_ax.add_artist(legend_right)  # ✅ 右も保持する（これが抜けていた）

    # タイトルなどの余白
    #fig.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.05)
    fig.subplots_adjust(left=0.05, right=0.95, top=0.92, bottom=0.08)
    chart_path = f"chart_{symbol}.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight")
    if show_plot:
        display(Image(chart_path))
    plt.close(fig)

    return chart_path

# ================================
# Sec6｜コメント・スコア処理
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

    return comment_map, score_dict

# ================================
# Sec7｜HTMLテーブル生成
# ================================

def get_style_by_comment(comment):
    """
    コメントのシグナル内容に応じて色・スタイルを返す
    """
    if not comment:
        return ""

    match = re.match(r"^(買[強弱]|売[強弱]|中立)[|｜]", comment)
    if not match:
        return ""

    signal = match.group(1)
    if signal == "中立":
        return ""

    color = "green" if "買" in signal else "red"
    weight = "bold" if "強" in signal else "normal"

    return f"color: {color}; font-weight: {weight}"

def apply_row_style(row):
    """
    コメント列の内容に応じたスタイルを適用（pandas Styler 用）
    """
    comment = row["コメント"]
    return [get_style_by_comment(comment) if col != "指標" else "" for col in row.index]

def generate_summary_html(df, comment_map, score_dict):
    """
    指標と7日分の値を表にまとめ、コメントとスコアを含めたHTMLを返す
    """
    df_recent_week = df.tail(7)
    date_labels = [d.strftime("%-m/%-d") for d in df_recent_week.index]

    table_data = []

    def extract_comment_text(key):
        entries = comment_map.get(key, [])
        if not entries:
            return ""
        entry = entries[0]
        return f"{entry['signal']}｜{entry['detail']} {entry['note']}".strip()

    def add_row(label, values):
        table_data.append([label] + values)

    add_row("株価（終値）", [f"{v:.2f}" for v in df_recent_week["Close"]])
    add_row("出来高", [f"{v/10000:.1f}万" for v in df_recent_week["Volume"]])
    add_row("RSI", [f"{v:.2f}" for v in df_recent_week["RSI"]])
    add_row("MACD", [f"{v:.2f}" for v in df_recent_week["MACD"]])
    add_row("ストキャス（%K）", [f"{v:.2f}" for v in df_recent_week["STOCH_K"]])
    add_row("ストキャス（%D）", [f"{v:.2f}" for v in df_recent_week["STOCH_D"]])
    add_row("ADX", [f"{v:.2f}" for v in df_recent_week["ADX"]])
    add_row("25日乖離率（%）", [f"{v:.2f}" for v in df_recent_week["MA25_Deviation"]])
    add_row("BB上限", [f"{v:.2f}" for v in df_recent_week["BB_High"]])
    add_row("BB中央", [f"{v:.2f}" for v in df_recent_week["BB_MAVG"]])
    add_row("BB下限", [f"{v:.2f}" for v in df_recent_week["BB_Low"]])

    # コメント列の追加
    comment_list = []
    for row in table_data:
        key = row[0]
        comment_list.append(extract_comment_text(key))

    df_table = pd.DataFrame(table_data, columns=["指標"] + date_labels)
    df_table["コメント"] = comment_list

    # スタイリング
    styled_df = df_table.style.apply(apply_row_style, axis=1)
    html_table = styled_df.to_html(render_links=False, escape=False)

    # スコアの視覚表現
    def score_bar(score):
        filled = int(round(score))
        return "■" * filled + "□" * (10 - filled)

    html_score = f"""
    <div style="text-align:center; background:#e0f0ff; padding:10px; font-weight:bold;">
        【総合評価】スコア: {sum(score_dict.values()):.1f} / 30点満点
    </div>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; font-family: monospace; margin-top:10px;">
        <thead style="background-color:#f0f0f0;">
            <tr>
                <th>カテゴリ</th><th>スコア</th><th>評価バー</th>
            </tr>
        </thead>
        <tbody>
            <tr><td>テクニカル</td><td>{score_dict['technical']:.1f}/10</td><td>{score_bar(score_dict['technical'])}</td></tr>
            <tr><td>チャート</td><td>{score_dict['chart']:.1f}/10</td><td>{score_bar(score_dict['chart'])}</td></tr>
            <tr><td>ファンダ</td><td>{score_dict['fundamental']:.1f}/10</td><td>{score_bar(score_dict['fundamental'])}</td></tr>
        </tbody>
    </table>
    """

    return f"""
    <html><head><meta charset="utf-8"></head>
    <body>
    {html_score}<br>{html_table}
    </body></html>
    """

# ================================
# Sec8｜チャート＋テーブル保存
# ================================

def save_combined_chart_and_table(chart_path, html_table, output_dir, symbol, name, today_str,
                                  table_image_path="table_temp.jpg", save_pdf=False):
    """
    チャート画像とHTMLテーブルを結合し、JPG（+任意でPDF）として保存する。
    """
    # 🔧 temp HTML保存
    with open("temp_table.html", "w", encoding="utf-8") as f:
        f.write(html_table)

    # 🔧 wkhtmltoimage のパス確認
    wkhtml_path = shutil.which("wkhtmltoimage") or "/usr/bin/wkhtmltoimage"
    if not os.path.exists(wkhtml_path):
        raise EnvironmentError("❌ wkhtmltoimage が見つかりません。Colab環境にインストールしてください")

    # 🔧 imgkit 設定
    config = imgkit.config(wkhtmltoimage=wkhtml_path)
    options = {
        'format': 'jpg',
        'encoding': "UTF-8",
        'custom-header': [('Accept-Encoding', 'gzip')],
        'quality': '85',
        'zoom': 2,
        'crop-w': 1600
    }

    try:
        imgkit.from_file("temp_table.html", table_image_path, config=config, options=options)
    except Exception as e:
        raise RuntimeError(f"❌ HTMLテーブル画像化に失敗しました: {e}")

    # 🔧 チャート画像とテーブル画像を結合
    chart_img = PILImage.open(chart_path)
    table_img = PILImage.open(table_image_path)

    def resize_to_width(img, target_width):
        w, h = img.size
        if w == target_width:
            return img
        new_h = int(h * (target_width / w))
        return img.resize((target_width, new_h), PILImage.LANCZOS)

    max_width = max(chart_img.width, table_img.width)
    chart_img = resize_to_width(chart_img, max_width)
    table_img = resize_to_width(table_img, max_width)

    combined_height = chart_img.height + table_img.height
    combined_img = PILImage.new("RGB", (max_width, combined_height), "white")
    combined_img.paste(chart_img, (0, 0))
    combined_img.paste(table_img, (0, chart_img.height))

    # 🔧 保存パス準備
    save_folder = os.path.join(output_dir, f"{symbol}_{name}")
    os.makedirs(save_folder, exist_ok=True)
    base_filename = f"{symbol}_{name}_{today_str}"
    jpg_path = os.path.join(save_folder, base_filename + ".jpg")

    # 🔧 JPG保存
    combined_img.save(jpg_path, optimize=True, quality=95)
    print(f"✅ 保存完了：{jpg_path}")

    # 🔧 PDF保存（オプション）
    if save_pdf:
        pdf_path = os.path.join(save_folder, base_filename + ".pdf")
        combined_img.convert("RGB").save(pdf_path, "PDF", resolution=100.0)
        print(f"📄 PDF保存完了：{pdf_path}")
    # ✅ 保存パスを返す（← これがないと None 扱いになる）
    return jpg_path

# ================================
# Sec9｜メイン実行ループ
# ================================
from matplotlib import font_manager
from datetime import datetime, timedelta, timezone

# ✅ 日本語フォント設定
font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
jp_font = font_manager.FontProperties(fname=font_path)

def main():
    JST = timezone(timedelta(hours=9))
    today_str = datetime.now(JST).strftime("%Y-%m-%d")

    setup_environment()
    symbols = get_symbol_list()

    for symbol in symbols:
        try:
            df, name = get_stock_data(symbol)
            if df is None:
                continue
            df = add_technical_indicators(df)
            df_recent = df.tail(60).copy()

            # ✅ データが少ない銘柄はスキップ
            if len(df_recent) < 10:
                print(f"⚠️ {symbol} はデータ不足のためスキップ（{len(df_recent)}行）")
                continue

            # ✅ 本格チャート生成
            print("📈 generate_full_stock_chart を呼び出し")
            chart_path = generate_full_stock_chart(df_recent, symbol, name, today_str, jp_font)

            comment_map, score_dict = evaluate_indicators(df)
            html_table = generate_summary_html(df, comment_map, score_dict)

            save_combined_chart_and_table(
                chart_path=chart_path,
                html_table=html_table,
                output_dir="/content/drive/MyDrive/ColabNotebooks/銘柄分析",
                symbol=symbol,
                name=name,
                today_str=today_str,
                save_pdf=False
            )

        except Exception as e:
            print(f"❌ {symbol} でエラー発生: {e}")

def main():
    # タイムゾーンと日付
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    today_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    setup_environment()
    symbols = get_symbol_list()

    log_lines = []
    log_lines.append(f"📌 実行日時: {timestamp}")
    log_lines.append(f"📊 処理対象: {len(symbols)}銘柄")
    log_lines.append("")

    # 実行時間計測開始
    start_time = time.time()

    for symbol in symbols:
        name = "不明"  # ← 初期化
        start_symbol = time.time()
        try:
            df, name = get_stock_data(symbol)
            if df is None:
                raise ValueError("データ取得失敗")

            df = add_technical_indicators(df)
            df_recent = df.tail(60).copy()

            chart_path = plot_stock_chart(df_recent, symbol, name, today_str, jp_font)
            comment_map, score_dict = evaluate_indicators(df)
            html_table = generate_summary_html(df, comment_map, score_dict)

            save_path = save_combined_chart_and_table(
                chart_path=chart_path,
                html_table=html_table,
                output_dir="/content/drive/MyDrive/ColabNotebooks/銘柄分析",
                symbol=symbol,
                name=name,
                today_str=today_str,
                save_pdf=False
            )

            elapsed_symbol_time = time.time() - start_symbol
            log_lines.append(f"✅ 成功: {symbol} - {name} | 📂 保存: {save_path}")
            log_lines.append(f"⏱ 所要時間: {elapsed_symbol_time:.2f}秒")

        except Exception as e:
            log_lines.append(f"❌ 失敗: {symbol} - {name} | {type(e).__name__}: {e}")

    # 実行時間計測終了
    elapsed_time = time.time() - start_time
    log_lines.append(f"⏱ 全体所要時間: {elapsed_time:.2f}秒")

    # ログ保存
    log_dir = "/content/drive/MyDrive/ColabNotebooks/銘柄分析/Log"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"log_{today_str}.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
        f.write("\n" + "=" * 50 + "\n")

    print(f"📝 処理ログを保存しました: {log_path}")
    print(f"⏱ 全体所要時間: {elapsed_time:.2f}秒")

# ==============================
# ✅ 実行開始（ColabではこれでOK）
# ==============================
main()