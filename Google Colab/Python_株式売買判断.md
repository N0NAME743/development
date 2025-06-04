##### Memo
📘 日本株スイングトレード分析スクリプト

[仕組み]
1.Googleドライブに保存しているスプレット上に「銘柄コード」を入力
2.Google Colab上で、このスクリプトを実行すると
    「株価データ」、「テクニカル情報」などを（表＋チャート）画像として、出力
[実装機能]
    ver1.00
    ・Googleドライブとの連携
    ver1.01
    ・表示フラグで、画像の保存オン・オフ機能を実装
    ver1.02
    ・コードの見栄えを少し修正した。
    ・外部ファイルのコードを末尾に追記
    ver1.10
    ・サポートライン、レジスタラインをグラフ上に追記
    ・ピポットポイントをグラフ上に追記
    ・チャートのコードを修正した。
    ver1.11
    ・チャートグラフの内容を大幅に修正した。
    ・チャート表示のデバッグコードを追加した。
    ・ボリンジャーバンドの表示を追加した➡非表示（デフォルト）
    ver1.20｜コード修正途中
    ・コードの中身を整えて、不要なコード等を削除した。
    ・旧テーブル表記（Styler）を削除し、HTMLテーブルで画像の保存処理を作った。
    ver1.21
    ・コードの順序を整理した。
    ・チャートの表示を微調整＋タイトル／サブタイトルを表示するようにした。
    ver.1.22
    ・総合評価の部分を末尾から「チャート」、「表」の真ん中に移動させた。
    ・スコアのコードを自動で算出するようにした（※要調整）
[未実装機能]
    ・各指標（例：短期GC, MACD上昇, RSIが中立など）の組み合わせが過去にどれくらいの確率で勝てたか（＝終値が上がったか）を元に、
    「今回のシグナルの信頼度（スコア）」を出力するのが目的です。
    ・
##### Memo_END

######### 0.Condig（設定）

import imgkit
import io
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import os
import pandas as pd
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

## 日本語フォント設定
font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
jp_font = font_manager.FontProperties(fname=font_path)
plt.rcParams['font.family'] = jp_font.get_name()  # NotoSansCJK に切り替え
pil_font = ImageFont.truetype(font_path, 24)

## タイムゾーンと日付
JST = timezone(timedelta(hours=9))
today_str = datetime.now(JST).strftime("%Y-%m-%d")

## Google Driveマウント
from google.colab import drive
drive.mount('/content/drive')

## 銘柄リスト取得
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQZrqf2NhMcD6ebNirrxSV_ibn1FTn2Rj-jrRI27nQcSEAgkqEQfvEZYitYoB1GT65S7qIrgGhMds1i/pub?gid=0&single=true&output=csv"
df_symbols = pd.read_csv(sheet_url)
symbols = df_symbols["Symbol"].dropna().tolist()
print("🔌 対象銘柄：", symbols)

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

## 定義・関数
# 1. ユーティリティ系関数：数値をK/M/Bで省略表示
def abbreviate_number(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return str(n)
# 2. コメント生成関数

def generate_summary_comment(comment_map, score):
    buy_comments = []
    sell_comments = []

    for key, comment in comment_map.items():
        # 条件分岐してコメント分類
        ...

    if score >= 5:
        summary = "..."
    elif score >= 2:
        summary = "..."
    elif score <= -5:
        summary = "..."
    elif score <= -2:
        summary = "..."
    else:
        summary = "..."

    html = "<div>...</div>"
    return html


def generate_summary_comment(comment_map, score):
    buy_comments = []
    sell_comments = []

    # 買い・売りコメントを整理
    for key, comment in comment_map.items():
        if "買い" in comment:
            buy_comments.append(f"<li>{key}：{comment}</li>")
        elif "売り" in comment:
            sell_comments.append(f"<li>{key}：{comment}</li>")

    # 総評コメントのロジック（戦略提案込み）
    if score >= 5:
        summary = ("強い買いシグナルが複数確認され、上昇トレンドが明確です。"
                  "短期の押し目を狙った買いが有効と考えられます。")
    elif score >= 2:
        summary = ("買いシグナルがやや優勢で、反転の兆しが見え始めています。"
                  "ただし、出来高や過熱感に注意しながら、慎重なエントリーを心がけましょう。")
    elif score <= -5:
        summary = ("複数の売りシグナルにより、明確な下落トレンドが形成されています。"
                  "ここでのエントリーは避け、反発の兆候が見えるまで様子を見る戦略が賢明です。")
    elif score <= -2:
        summary = ("売りシグナルがやや優勢で、下方向へのリスクが高まっています。"
                  "ポジションを軽くするか、新規エントリーは見送るのが安全です。")
    else:
        summary = ("買い・売りが拮抗しており、明確な方向感に欠ける相場です。"
                  "トレンドが明確になるまで静観し、過剰な取引を避けましょう。")

    # HTML形式で見やすく出力
    html = "<div style='font-size:14px; line-height:1.6em;'>"
    if buy_comments:
        html += "<b>🟢 買い目線の要因：</b><ul>" + "".join(buy_comments) + "</ul><br>"
    if sell_comments:
        html += "<b>🔴 売り目線の要因：</b><ul>" + "".join(sell_comments) + "</ul><br>"
    html += f"<b>⚖️ 総評と戦略：</b><p>{summary}</p></div>"

    return html

# 3. チャート＋テーブル保存関数
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
    imgkit.from_file("temp_table.html", table_image_path, config=config, options=options)

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
    combined_img.save(jpg_path, optimize=True, quality=85)
    print(f"✅ JPGとして保存しました：{jpg_path}")

    # ✅ PDF保存（オプション）
    if save_pdf:
        pdf_path = os.path.join(save_folder, base_filename + ".pdf")
        combined_img.convert("RGB").save(pdf_path, "PDF", resolution=100.0)
        print(f"📄 PDFとしても保存しました：{pdf_path}")


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
            adx = ADXIndicator(df["High"], df["Low"], df["Close"])
            df["ADX"] = adx.adx()
        if SHOW_STOCH:
            stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
            df["STOCH_K"] = stoch.stoch()
            df["STOCH_D"] = stoch.stoch_signal()
        if SHOW_MA_DEVIATION:
            df["MA25_Deviation"] = (df["Close"] - df["MA25"]) / df["MA25"] * 100
        df_filtered = df.dropna().copy()
        df_recent = df_filtered[-60:]
        df_recent = df_recent.copy()
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

        # チャート描画
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
        subtitle = f"対象期間：{df.index[0].strftime('%Y/%m/%d')} ～ {df.index[-1].strftime('%Y/%m/%d')}｜傾向：下降トレンド継続中"
        # axlist[0] 上部にテキスト追加（座標: x=0.5, y=1.08 は上部中央）
        axlist[0].text(
            0.5, 1.07,  # X, Y（0～1の相対値）
            subtitle,
            transform=axlist[0].transAxes,  # 軸に対して相対位置
            ha='center',                    # 水平中央揃え
            va='top',                       # 垂直上揃え
            fontsize=12,
            fontproperties=jp_font,
            color='dimgray'
        )
        fig.subplots_adjust(left=0.05, right=0.95)
        fig.savefig("chart_output.png", dpi=150, bbox_inches="tight")

        # サポート・レジスタンスライン
        price_ax = axlist[0]
        sr_windows = [20, 60]
        support_colors = ["#1f77b4", "#17becf"]
        resistance_colors = ["#d62728", "#ff7f0e"]
        x_pos = len(df_recent) + 1
        for idx, window in enumerate(sr_windows):
            if len(df_recent) >= window:
                support = df_recent["Low"].rolling(window).min().iloc[-1]
                resist = df_recent["High"].rolling(window).max().iloc[-1]
                price_ax.axhline(support, color=support_colors[idx % 2], linestyle='--', linewidth=1.2, alpha=0.8)
                price_ax.axhline(resist, color=resistance_colors[idx % 2], linestyle='--', linewidth=1.2, alpha=0.8)
                price_ax.text(x_pos, support, f"\u2190 Support ({window}d)", va='center', fontsize=8, color=support_colors[idx % 2])
                price_ax.text(x_pos, resist, f"\u2190 Resistance ({window}d)", va='center', fontsize=8, color=resistance_colors[idx % 2])

        # 凡例表示（ラベル付きの要素があるときのみ）
        if any(line.get_label() and not line.get_label().startswith("_") for line in price_ax.lines):
            price_ax.legend(loc='upper left', fontsize='small')

        # RSI表示設定
        target_rsi_ax = next((ax for ax in axlist if ax.get_ylabel() == "RSI"), None)
        if target_rsi_ax:
            target_rsi_ax.set_ylim(0, 100)
            target_rsi_ax.set_yticks([20, 40, 60, 80])
            target_rsi_ax.axhline(80, color='red', linestyle='--', linewidth=1)
            target_rsi_ax.axhline(20, color='blue', linestyle='--', linewidth=1)

        # レイアウトと保存
        try:
            fig.tight_layout()
        except Exception as e:
            print(f"[警告] tight_layout に失敗しました: {e}")
        chart_path = f"{symbol}_{name}_{today_str}.png"
        if SHOW_SAVE_CHART:
            # ✅ tight_layout は必ず保存前に呼ぶ
            fig.tight_layout()
            fig.savefig(chart_path, dpi=150)
            plt.close(fig)
        if not os.path.exists(chart_path):
            raise FileNotFoundError(f"チャート画像の保存に失敗しました: {chart_path}")

######### 2.チャート-END

######### 3.コメント（指標判断）-START

        # コメントマップに安全かつ統一的に登録する関数

        def add_comment(comment_map, key, signal, detail, note=""):
            icon = {"買い": "🟢", "売り": "🔴", "中立": "🟡"}.get(signal, "")
            full_note = f" {note}" if note else ""
            comment_map[key] = f"{signal}｜{detail}{full_note}".strip()

        # 信頼度の分類とノートフォーマット関数
        def judge_strength(gap_value, thresholds):
            if gap_value > thresholds["強"]:
                return "強"
            elif gap_value > thresholds["中"]:
                return "中"
            else:
                return "弱"

        def format_note(strength, vol_increased):
            vol_note = "出来高増" if vol_increased else ""
            return f"[信頼度{strength}/{vol_note}]" if vol_note else f"[信頼度{strength}]"

        # 利用例
        score = 0
        comment_map = {}

        # ========= 1. データ取得と整形 =========
        # df_recent_week の定義
        df_recent_week = df.tail(7)

        # ========= 2. 最新・前日データの抽出 =========
        # 最新・前日データの定義
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # 株価終値・出来高
        diff = latest["Close"] - previous["Close"]
        add_comment(comment_map, "株価（終値）", "中立", f"終値={latest['Close']:.2f}（前日比{diff:+.2f}）")

        vol_latest = latest["Volume"]
        vol_avg = df_recent_week["Volume"].mean()
        diff = vol_latest - vol_avg
        pct = round((diff / vol_avg) * 100, 1)
        add_comment(comment_map, "出来高", "中立", f"7日平均={vol_avg:,.0f}（差分={diff:+,.0f} / {pct:+.1f}%）")

        # 移動平均クロスの例（追加）
        ma_pairs = [
            ("5DMA", "25DMA", latest["MA5"], latest["MA25"], previous["MA5"], previous["MA25"], "短期"),
            ("25DMA", "75DMA", latest["MA25"], latest["MA75"], previous["MA25"], previous["MA75"], "中期"),
            ("75DMA", "200DMA", latest["MA75"], latest["MA200"], previous["MA75"], previous["MA200"], "長期")
        ]
        for key, base_key, cur, base, cur_prev, base_prev, label in ma_pairs:
            gap = (cur - base) / base * 100
            diff = cur - base
            relation = f"{key} > {base_key}" if diff > 0 else f"{key} < {base_key}"
            diff_str = f"{relation}, 差分={diff:+.2f}円"
            crossed_up = cur > base and cur_prev <= base_prev
            crossed_down = cur < base and cur_prev >= base_prev
            if crossed_up:
                strength = judge_strength(gap, thresholds)
                strength = {"弱": "中", "中": "強", "強": "最強"}[strength] if vol_increased else strength
                note = format_note(strength, vol_increased)
                add_comment(comment_map, key, "買い", f"{label}GC（{diff_str}）", note)
                score += {"弱": 1, "中": 2, "強": 3, "最強": 4}[strength]
            elif crossed_down:
                gap = abs(gap)
                strength = judge_strength(gap, thresholds)
                strength = {"弱": "中", "中": "強", "強": "最強"}[strength] if vol_increased else strength
                note = format_note(strength, vol_increased)
                add_comment(comment_map, key, "売り", f"{label}DC（{diff_str}）", note)
                score -= {"弱": 1, "中": 2, "強": 3, "最強": 4}[strength]
            else:
                add_comment(comment_map, key, "中立", f"明確なクロスなし（{diff_str}）")

        # 超GC / 超DC 判定
        ma5, ma25, ma75 = latest["MA5"], latest["MA25"], latest["MA75"]
        diff_super = ma5 - ma75
        diff_str_super = f"差分={diff_super:+.2f}円"
        if ma5 > ma25 > ma75:
            add_comment(comment_map, "超GC", "買い", f"超GC（5DMA > 25DMA > 75DMA, {diff_str_super}）", "[信頼度最強]")
            score += 4
        elif ma5 < ma25 < ma75:
            add_comment(comment_map, "超DC", "売り", f"超DC（5DMA < 25DMA < 75DMA, {diff_str_super}）", "[信頼度最強]")
            score -= 4
        else:
            if ma5 > ma25 and ma25 < ma75:
                trend_desc = "5DMA > 25DMA < 75DMA"
            elif ma5 < ma25 and ma25 > ma75:
                trend_desc = "5DMA < 25DMA > 75DMA"
            elif ma5 > ma75 and ma25 < ma75:
                trend_desc = "5DMA > 75DMA > 25DMA"
            else:
                trend_desc = "順序バラバラ"
            add_comment(comment_map, "超GC/DC", "中立", f"明確なシグナルなし（{trend_desc}, {diff_str_super}）")

        # 25日乖離率
        dev = latest["MA25_Deviation"]
        if dev > 5:
            add_comment(comment_map, "25日乖離率（%）", "売り", "平均より大きく上振れ（過熱感あり）")
        elif dev < -5:
            add_comment(comment_map, "25日乖離率（%）", "買い", "平均より大きく下振れ（割安感あり）")
        else:
            add_comment(comment_map, "25日乖離率（%）", "中立", "平均付近で安定")

        # ボリンジャーバンド
        diff_from_mid = latest["Close"] - latest["BB_MAVG"]
        band_width = latest["BB_High"] - latest["BB_Low"]
        deviation = (latest["Close"] - latest["BB_Low"]) / band_width * 100
        if latest["Close"] > latest["BB_High"]:
            add_comment(comment_map, "BB上限", "売り", f"{latest['Close']:.2f}円（終値） > BB上限={latest['BB_High']:.2f}円｜バンドを上抜け（買われすぎ）🚨")
        elif latest["Close"] < latest["BB_Low"]:
            add_comment(comment_map, "BB下限", "買い", f"{latest['Close']:.2f}円（終値） < BB下限={latest['BB_Low']:.2f}円｜バンドを下抜け（売られすぎ）📉")
        else:
            zone = "上寄り（やや割高）" if deviation > 66 else "下寄り（やや割安）" if deviation < 33 else "中央付近（安定圏）"
            add_comment(comment_map, "BB中央", "中立", f"{latest['Close']:.2f}円（終値）はバンド内の{zone}｜中心乖離={diff_from_mid:+.2f}円")

        # RSI
        val, prev_val = latest["RSI"], previous["RSI"]
        diff = val - prev_val
        trend = "上昇中" if diff > 0 else "低下中"
        if val > 80:
            strength = "強" if val >= 82 else "中" if val >= 81 else "弱"
            add_comment(comment_map, "RSI", "売り", f"買われすぎ（{trend} / 過熱度：{strength}）")
        elif val < 20:
            strength = "強" if val <= 18 else "中" if val <= 19 else "弱"
            add_comment(comment_map, "RSI", "買い", f"売られすぎ（{trend} / 割安度：{strength}）")
        else:
            add_comment(comment_map, "RSI", "中立", f"明確なシグナルなし（{trend} / 前日比{diff:+.2f}）")

        # ストキャス（%K）
        k, d = latest["STOCH_K"], latest["STOCH_D"]
        if k < 20 and k > d:
            add_comment(comment_map, "ストキャス（%K）", "買い", "売られすぎ圏から反転の兆し")
        elif k > 80 and k < d:
            add_comment(comment_map, "ストキャス（%K）", "売り", "買われすぎ圏から反落の兆し")
        else:
            zone = "売られすぎ圏" if k < 20 else "買われすぎ圏" if k > 80 else "中立圏"
            crossover = "ゴールデンクロス（上抜け）" if k > d else "デッドクロス（下抜け）" if k < d else "一致"
            add_comment(comment_map, "ストキャス（%K）", "中立", f"%K={k:.2f}｜{zone}で{k:.2f}（{crossover}）")

        # ストキャス（%D）
        d_val, prev_d_val = latest["STOCH_D"], previous["STOCH_D"]
        if d_val > 80:
            add_comment(comment_map, "ストキャス（%D）", "売り", "買われすぎ圏に滞在")
        elif d_val < 20:
            add_comment(comment_map, "ストキャス（%D）", "買い", "売られすぎ圏に滞在")
        else:
            add_comment(comment_map, "ストキャス（%D）", "中立", "明確なサインなし")

        # ストキャス総合
        k, d = latest["STOCH_K"], latest["STOCH_D"]
        if k < 20 and k > d:
            add_comment(comment_map, "ストキャス総合", "買い", "売られすぎ圏でGC発生")
            score += 1
        elif k > 80 and k < d:
            add_comment(comment_map, "ストキャス総合", "売り", "買われすぎ圏でDC発生")
            score -= 1
        elif k > d and k < 50:
            add_comment(comment_map, "ストキャス総合", "中立", "中立〜買い寄り｜下位圏で上昇中")
        elif k < d and k > 50:
            add_comment(comment_map, "ストキャス総合", "中立", "中立〜売り寄り｜上位圏で下落中")
        else:
            add_comment(comment_map, "ストキャス総合", "中立", "明確なシグナルなし")

        # MACD
        val, prev_val = latest["MACD_Diff"], previous["MACD_Diff"]
        diff = val - prev_val
        if val > 0:
            if diff > 0:
                add_comment(comment_map, "MACD", "買い", "MACD上昇中（勢い強）")
            else:
                add_comment(comment_map, "MACD", "買い", "MACDプラス圏だが減速中（慎重に）")
        else:
            if diff < 0:
                add_comment(comment_map, "MACD", "売り", "MACD下降中（勢い強）")
            else:
                add_comment(comment_map, "MACD", "売り", "MACDマイナス圏だが減速中（様子見）")

        # ADX
        val = latest["ADX"]
        if val < 20:
            add_comment(comment_map, "ADX", "中立", "方向感なし（様子見）")
        elif val < 25:
            add_comment(comment_map, "ADX", "中立", "転換｜トレンド発生の兆し（注目）")
        elif val < 40:
            add_comment(comment_map, "ADX", "中立", "追随｜トレンド発生中（流れに乗る場面）")
        else:
            add_comment(comment_map, "ADX", "中立", "過熱｜トレンド過熱（反転に注意）")

        # 総合評価
        comment_map["✅ 総合評価"] = f"スコア: {score:.1f}"

######### 3.コメント（指標判断）-END

######### 4.テーブル-START

        # 表データの作成
        df_recent_week = df_filtered[-7:]
        date_labels = [d.strftime("%-m/%-d") for d in df_recent_week.index]
        divider = lambda name: [f"── {name} ──"] + ["" for _ in df_recent_week.index]
        table_data = []
        table_data.append(["株価（終値）"] + [f"{v:.2f}" for v in df_recent_week["Close"]])
        table_data.append(["出来高"] + [abbreviate_number(v) for v in df_recent_week["Volume"]])
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

        # コメントにアイコンを付与
        def emphasize(val):
            if "買い" in val:
                return f"🟢 {val}"
            elif "売り" in val:
                return f"🔴 {val}"
            elif "中立" in val:
                return f"🟡 {val}"
            return val

        # コメント列を追加
        comment_list = [emphasize(comment_map.get(row[0], "")) for row in table_data]
        df_table["コメント"] = comment_list

        # CSS（コメント列を左寄せ）
        style = """
        <style>
        table {
          border-collapse: collapse;
          width: auto;  /* 👈 これに変更！ */
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

        # ✅ 初期化
        summary_text = "⚠️ 総合評価：評価情報が取得できません（スコア未算出）"
        score = 0.0

        # ✅ 安全にスコアを抽出
        if "✅ 総合評価" in comment_map:
            try:
                score = float(comment_map["✅ 総合評価"].split("スコア:")[-1])
                summary_text = generate_summary_comment(score)
            except Exception as e:
                print(f"⚠️ 評価の解析中にエラーが発生: {e}")
        else:
            print(f"⚠️ {symbol} - '✅ 総合評価' が見つかりません")

        # ✅ 総合評価コメントを動的に生成
        def generate_summary_comment(score):
            if score >= 7:
                return f"✅ 総合評価：買い傾向（スコア: {score:.1f}）"
            elif score >= 4:
                return f"⚠️ 総合評価：やや買い（スコア: {score:.1f}）"
            elif score >= 1:
                return f"😐 総合評価：中立（スコア: {score:.1f}）"
            elif score >= -2:
                return f"⚠️ 総合評価：やや売り（スコア: {score:.1f}）"
            else:
                return f"❌ 総合評価：売り傾向（スコア: {score:.1f}）"

        # ✅ scoreから生成された summary_text を使う
        colspan = len(df_table.columns)
        summary_row = f'<tr><td colspan="{colspan}" style="text-align:center; font-weight:bold; background:#eef;">{summary_text}</td></tr>'

        # ✅ HTMLパーツに反映
        summary_html = f"""
        <p style="text-align:center; font-weight:bold; background:#eef; padding: 6px;">
        {summary_text}
        </p>
        """
        summary_row = f'<tr><td colspan="{colspan}" style="text-align:center; font-weight:bold; background:#eef;">{summary_text}</td></tr>'

        # ✅ テーブル末尾には評価行を追加しない
        html_table_with_summary = df_table.to_html(index=False, escape=False)

        # ✅ 表全体のHTML構造
        html_table = f"""
        <html>
        <head>
        <meta charset="utf-8">
        {style}  <!-- ✅ CSS -->
        </head>
        <body>
        <h4>{name}（{symbol}）｜取得日: {today_str}</h4>
        {html_table_with_summary}
        </body>
        </html>
        """
        # ✅ 表示順を指定
        display(Image(chart_path))          # ① チャート
        display(HTML(summary_html))         # ② 総合評価だけ別表示（中間に！）
        display(HTML(html_table))           # ③ テーブル全体

        # 👉 関数に渡すときはこれ！
        save_combined_chart_and_table(
            chart_path=chart_path,
            html_table=html_table,  # ← ここを修正
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
