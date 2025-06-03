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

[未実装機能]
    ・各指標（例：短期GC, MACD上昇, RSIが中立など）の組み合わせが過去にどれくらいの確率で勝てたか（＝終値が上がったか）を元に、
    「今回のシグナルの信頼度（スコア）」を出力するのが目的です。
    ・

##### Memo_END

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
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands
from ta import momentum
from tabulate import tabulate

# ✅ 日本語フォント設定
font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
jp_font = font_manager.FontProperties(fname=font_path)

# ✅ matplotlib に日本語フォントを設定
plt.rcParams['font.family'] = jp_font.get_name()  # NotoSansCJK に切り替え

# ✅ PIL用フォント設定（表画像に使う用）
from PIL import ImageFont
pil_font = ImageFont.truetype(font_path, 24)

# タイムゾーンと日付
JST = timezone(timedelta(hours=9))
today_str = datetime.now(JST).strftime("%Y-%m-%d")

# Google Driveマウント
from google.colab import drive
drive.mount('/content/drive')

# 銘柄リスト取得
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQZrqf2NhMcD6ebNirrxSV_ibn1FTn2Rj-jrRI27nQcSEAgkqEQfvEZYitYoB1GT65S7qIrgGhMds1i/pub?gid=0&single=true&output=csv"
df_symbols = pd.read_csv(sheet_url)
symbols = df_symbols["Symbol"].dropna().tolist()
print("🔌 対象銘柄：", symbols)

# 表示フラグ
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

# チャート＋テーブル画像統合保存関数
def save_combined_image(chart_path, table_text, output_path):
    font = ImageFont.truetype(font_path, 24)
    lines = table_text.split("\n")
    padding = 10
    max_width = 1600
    image_height = 35 * len(lines)
    table_img = PILImage.new("RGB", (int(max_width), image_height + 2 * padding), "white")
    draw = ImageDraw.Draw(table_img)
    for i, line in enumerate(lines):
        draw.text((padding, i * 35 + padding), line, fill="black", font=font)
    chart_img = PILImage.open(chart_path)
    new_width = max(chart_img.width, table_img.width)
    new_height = chart_img.height + table_img.height
    combined_img = PILImage.new("RGB", (new_width, new_height), "white")
    combined_img.paste(chart_img, (0, 0))
    combined_img.paste(table_img, (0, chart_img.height))
    combined_img.save(output_path)

# ✅ ユーティリティ関数：数値をK/M/Bで省略表示
def abbreviate_number(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return str(n)

######### 1.ループ-START- #########

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
        if df_recent.empty:
            print(f"⚠️ {symbol} はデータ不足でスキップ")
            continue

######### 2.チャート-START- #########

        add_plots = []
        panel_ratios = [2]  # panel=0: メインチャート（ローソク足）
        panel_id = 1  # 次に追加する panel 番号

        # 例：出来高移動平均（フラグON時のみ追加）
        if SHOW_VOLUME_MA:
            add_plots += [
                mpf.make_addplot(df_recent["Vol_MA5"], panel=panel_id, color="blue"),
                mpf.make_addplot(df_recent["Vol_MA25"], panel=panel_id, color="orange")
            ]
            panel_ratios.append(1)
            panel_id += 1

        # 例：RSI（フラグON時のみ追加）
        if SHOW_RSI:
            add_plots.append(mpf.make_addplot(df_recent["RSI"], panel=panel_id, ylabel="RSI"))
            panel_ratios.append(1)
            panel_id += 1

        # 例：MACD（フラグON時のみ追加）
        if SHOW_MACD:
            add_plots += [
                mpf.make_addplot(df_recent["MACD"], panel=panel_id, color="black", ylabel="MACD"),
                mpf.make_addplot(df_recent["MACD_Signal"], panel=panel_id, color="red"),
                mpf.make_addplot(df_recent["MACD_Diff"], panel=panel_id, color="blue")
            ]
            panel_ratios.append(1)
            panel_id += 1

        # ✅ ピボットポイントの検出（df_recentベースに変更）
        price = df_recent["Close"].values
        high_idx = argrelextrema(price, np.greater, order=5)[0]
        low_idx = argrelextrema(price, np.less, order=5)[0]
        # ✅ 全体長と整合するマーカー配列を作成
        high_marker = np.full(len(df_recent), np.nan)
        low_marker = np.full(len(df_recent), np.nan)
        high_marker[high_idx] = price[high_idx]
        low_marker[low_idx] = price[low_idx]
        # ✅ ピボットポイントを scatter プロットとして追加
        add_plots += [
            mpf.make_addplot(high_marker, type='scatter', markersize=100, marker='^', color='red'),
            mpf.make_addplot(low_marker, type='scatter', markersize=100, marker='v', color='blue'),
        ]
        # メインチャート軸に注釈（optional）
        price_ax = axlist[0]
        price_ax.legend(["High Pivot", "Low Pivot"], loc="upper left", fontsize="small")

        fig, axlist = mpf.plot(
            df_recent,
            type="candle",
            style="yahoo",
            volume=False,
            addplot=add_plots,
            panel_ratios=panel_ratios,
            returnfig=True,
            figsize=(12, 6)
        )

        # 例：1600ピクセル幅に揃えたい場合
        fig.set_size_inches(1600 / 150, 600 / 150)  # dpi=150の場合、インチ = ピクセル ÷ dpi

        # ✅ 正しいサポート／レジスタンスライン描画 + 注釈表示（インデックス指定対応版）
        price_ax = axlist[0]  # メインチャート軸
        # 使用する日数
        sr_windows = [20, 60]
        # 色設定
        support_colors = ["#1f77b4", "#17becf"]
        resistance_colors = ["#d62728", "#ff7f0e"]
        # ✅ インデックス位置ベースで注釈を描画する
        x_pos = len(df_recent) + 1  # グラフの右端ちょい先
        for idx, window in enumerate(sr_windows):
            if len(df_recent) >= window:
                support_level = df_recent["Low"].rolling(window=window).min().iloc[-1]
                resistance_level = df_recent["High"].rolling(window=window).max().iloc[-1]
                sup_color = support_colors[idx % len(support_colors)]
                res_color = resistance_colors[idx % len(resistance_colors)]
                # ライン描画
                price_ax.axhline(support_level, color=sup_color, linestyle='--', linewidth=1.2,
                                alpha=0.8, label=f'Support ({window}d)')
                price_ax.axhline(resistance_level, color=res_color, linestyle='--', linewidth=1.2,
                                alpha=0.8, label=f'Resistance ({window}d)')
                # ✅ 注釈：X座標はインデックスで指定
                price_ax.text(
                    x_pos, support_level, f'← Support ({window}d)',
                    verticalalignment='center', fontsize=8, color=sup_color
                )
                price_ax.text(
                    x_pos, resistance_level, f'← Resistance ({window}d)',
                    verticalalignment='center', fontsize=8, color=res_color
                )
        # 凡例
        price_ax.legend(loc='upper left', fontsize='small')

        # ✅ 日本語フォントをすべてのAxesとTextに適用（savefig直前）
        for ax in fig.axes:
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(jp_font)
            if ax.title:  # タイトルがある場合
                ax.title.set_fontproperties(jp_font)
            if ax.xaxis.label:  # X軸ラベル
                ax.xaxis.label.set_fontproperties(jp_font)
            if ax.yaxis.label:  # Y軸ラベル
                ax.yaxis.label.set_fontproperties(jp_font)

        # ✅ タイトルや取得日などの情報をグラフ上部に追加
        title = f"{name}（{symbol}）株価チャート（直近60日） - {today_str}"
        axlist[0].set_title(title, fontproperties=jp_font)

        # ✅ RSIチャートの描写設定（rsi_ax_indexが正しく設定されている前提）
        if rsi_ax_index is not None and rsi_ax_index < len(axlist):
            ax = axlist[rsi_ax_index]
            ax.set_ylim(0, 100)  # ← 表示範囲を固定
            ax.set_yticks([20, 40, 60, 80])  # ← 目盛りを20刻みに固定
            ax.axhline(80, color='red', linestyle='--', linewidth=1)
            ax.axhline(20, color='blue', linestyle='--', linewidth=1)

        # ✅ グラフ画像の保存
        chart_path = f"{symbol}_{name}_{today_str}.png"
        for text in fig.texts:
            text.set_fontproperties(jp_font)
        if SHOW_SAVE_CHART:
            fig.savefig(chart_path, dpi=150)
            plt.close(fig)
        if not os.path.exists(chart_path):
            raise FileNotFoundError(f"チャート画像の保存に失敗しました: {chart_path}")

######### 2.チャート-END- #########
######### 3.テーブル-START- #########

        # ✅ 表データの作成
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
        table_data.append(divider("トレンド系"))
        if SHOW_MACD:
            table_data.append(["MACD"] + [f"{v:.2f}" for v in df_recent_week["MACD"]])
        if SHOW_ADX:
            table_data.append(["ADX"] + [f"{v:.2f}" for v in df_recent_week["ADX"]])
        table_data.append(divider("オシレーター系"))
        if SHOW_RSI:
            table_data.append(["RSI"] + [f"{v:.2f}" for v in df_recent_week["RSI"]])
        if SHOW_STOCH:
            table_data.append(["ストキャス（%K）"] + [f"{v:.2f}" for v in df_recent_week["STOCH_K"]])
            table_data.append(["ストキャス（%D）"] + [f"{v:.2f}" for v in df_recent_week["STOCH_D"]])
        table_data.append(divider("ボラティリティ系"))
        if SHOW_BB:
            table_data.append(["BB上限"] + [f"{v:.2f}" for v in df_recent_week["BB_High"]])
            table_data.append(["BB中央"] + [f"{v:.2f}" for v in df_recent_week["BB_MAVG"]])
            table_data.append(["BB下限"] + [f"{v:.2f}" for v in df_recent_week["BB_Low"]])

        latest = df_recent_week.iloc[-1]
        previous = df_recent_week.iloc[-2]

        # ✅ コメント列作成
        comment_map = {}

        # ✅ コメント列統合
        def emphasize(val):
            if "買い" in val:
                return f"🟢 {val}"
            elif "売り" in val:
                return f"🔴 {val}"
            elif "中立" in val:
                return f"🟡 {val}"
            return val

  ######### 2-1.指標判断-START- #########

        # 株価（終値）
        if "Close" in latest and "Close" in previous:
            diff = latest["Close"] - previous["Close"]
            comment_map["株価（終値）"] = f"終値={latest['Close']:.2f}（前日比{diff:+.2f}）"
        # 出来高（平均）
        if "Volume" in latest and "Volume" in df_recent_week:
            vol_latest = latest["Volume"]
            vol_avg = df_recent_week["Volume"].mean()
            diff = vol_latest - vol_avg
            pct = round((diff / vol_avg) * 100, 1)
            comment_map["出来高"] = f"7日平均={vol_avg:,.0f}（差分={diff:+,.0f} / {pct:+.1f}%）"
        # ✅ 移動平均線-クロス判定（短期：5DMA vs 25DMA）
        if latest["MA5"] > latest["MA25"] and previous["MA5"] <= previous["MA25"]:
            gap = (latest["MA5"] - latest["MA25"]) / latest["MA25"] * 100
            if gap > 2:
                strength = "強"
            elif gap > 1:
                strength = "中"
            else:
                strength = "弱"
            comment_map["5DMA"] = f"買い｜短期ＧＣ（{gap:.2f}%乖離 / 信頼度{strength}）"
        elif latest["MA5"] < latest["MA25"] and previous["MA5"] >= previous["MA25"]:
            gap = (latest["MA25"] - latest["MA5"]) / latest["MA25"] * 100
            if gap > 2:
                strength = "強"
            elif gap > 1:
                strength = "中"
            else:
                strength = "弱"
            comment_map["5DMA"] = f"売り｜短期ＤＣ（{gap:.2f}%乖離 / 信頼度{strength}）"
        else:
            gap = abs(latest["MA5"] - latest["MA25"]) / latest["MA25"] * 100
            comment_map["5DMA"] = f"中立｜明確なシグナルなし（{gap:.2f}%差）"

        # ✅ 移動平均線-クロス判定（中期：25DMA vs 75DMA）
        if latest["MA25"] > latest["MA75"] and previous["MA25"] <= previous["MA75"]:
            gap = (latest["MA25"] - latest["MA75"]) / latest["MA75"] * 100
            if gap > 2.5:
                strength = "強"
            elif gap > 1.0:
                strength = "中"
            else:
                strength = "弱"
            comment_map["25DMA"] = f"買い｜中期ＧＣ（{gap:.2f}%乖離 / 信頼度{strength}）"
        elif latest["MA25"] < latest["MA75"] and previous["MA25"] >= previous["MA75"]:
            gap = (latest["MA75"] - latest["MA25"]) / latest["MA75"] * 100
            if gap > 2.5:
                strength = "強"
            elif gap > 1.0:
                strength = "中"
            else:
                strength = "弱"
            comment_map["25DMA"] = f"売り｜中期ＤＣ（{gap:.2f}%乖離 / 信頼度{strength}）"
        else:
            gap = abs(latest["MA25"] - latest["MA75"]) / latest["MA75"] * 100
            comment_map["25DMA"] = f"中立｜明確なシグナルなし（{gap:.2f}%差）"

        # ✅ 超ゴールデンクロス／デッドクロス
        if (
            latest["MA5"] > latest["MA25"] > latest["MA75"] and
            (previous["MA5"] <= previous["MA25"] or previous["MA5"] <= previous["MA75"])
        ):
            gap = (latest["MA5"] - latest["MA75"]) / latest["MA75"] * 100
            if gap > 2.5:
                strength = "強"
            elif gap > 1.0:
                strength = "中"
            else:
                strength = "弱"
            comment_map["超GC"] = f"買い｜超ＧＣ（5日→25日→75日 / {gap:.2f}%乖離 / 信頼度{strength}）"
        elif (
            latest["MA5"] < latest["MA25"] < latest["MA75"] and
            (previous["MA5"] >= previous["MA25"] or previous["MA5"] >= previous["MA75"])
        ):
            gap = (latest["MA75"] - latest["MA5"]) / latest["MA75"] * 100
            if gap > 2.5:
                strength = "強"
            elif gap > 1.0:
                strength = "中"
            else:
                strength = "弱"
            comment_map["超DC"] = f"売り｜超ＤＣ（5日→25日→75日 / {gap:.2f}%乖離 / 信頼度{strength}）"
        else:
            order = [latest["MA5"], latest["MA25"], latest["MA75"]]
            if order == sorted(order, reverse=True):
                trend_desc = "下降順序（5日＜25日＜75日）"
            elif order == sorted(order):
                trend_desc = "上昇順序（5日＞25日＞75日）"
            else:
                trend_desc = "順序バラバラ"
            gap = abs(latest["MA5"] - latest["MA75"]) / latest["MA75"] * 100
            comment_map["超GC/DC"] = f"中立｜明確なシグナルなし（{trend_desc} / 5日-75日差：{gap:.2f}％）"

        # ✅ 25日移動平均線からの乖離
        if "MA25_Deviation" in latest:
            dev = latest["MA25_Deviation"]
            if dev > 5:
                comment_map["25日乖離率（%）"] = f"売り｜平均より大きく上振れ（過熱感あり）"
            elif dev < -5:
                comment_map["25日乖離率（%）"] = f"買い｜平均より大きく下振れ（割安感あり）"
            else:
                comment_map["25日乖離率（%）"] = f"中立｜平均付近で安定"

        # ✅ MACD
        if "MACD_Diff" in latest and "MACD_Diff" in previous:
            val, prev_val = latest["MACD_Diff"], previous["MACD_Diff"]
            diff = val - prev_val
            if val > 0:
                if diff > 0:
                    signal = "買い｜MACD上昇中（勢い強）"
                else:
                    signal = "買い｜MACDプラス圏だが減速中（慎重に）"
            else:
                if diff < 0:
                    signal = "売り｜MACD下降中（勢い強）"
                else:
                    signal = "売り｜MACDマイナス圏だが減速中（様子見）"
            comment_map["MACD"] = f"{signal}"

        # ✅ ADX
        if "ADX" in latest:
            val = latest["ADX"]
            if val < 20:
                comment_map["ADX"] = f"中立｜方向感なし（様子見）"
            elif val < 25:
                comment_map["ADX"] = f"🟡 転換｜トレンド発生の兆し（注目）"
            elif val < 40:
                comment_map["ADX"] = f"🟡 追随｜トレンド発生中（流れに乗る場面）"
            else:
                comment_map["ADX"] = f"🟡 過熱｜トレンド過熱（反転に注意）"

        # ✅ RSI
        if "RSI" in latest and "RSI" in previous:
            val, prev_val = latest["RSI"], previous["RSI"]
            diff = val - prev_val
            trend = "上昇中" if diff > 0 else "低下中"

            if val > 80:
                if val >= 82:
                    strength = "強"
                elif val >= 81:
                    strength = "中"
                else:
                    strength = "弱"
                comment_map["RSI"] = f"売り｜買われすぎ（{trend} / 過熱度：{strength}）"
            elif val < 20:
                if val <= 18:
                    strength = "強"
                elif val <= 19:
                    strength = "中"
                else:
                    strength = "弱"
                comment_map["RSI"] = f"買い｜売られすぎ（{trend} / 割安度：{strength}）"
            else:
                comment_map["RSI"] = f"中立｜明確なシグナルなし（{trend} / 前日比{diff:+.2f}）"

        # ✅ ストキャスティクス
        if "STOCH_K" in latest and "STOCH_D" in latest:
            k, d = latest["STOCH_K"], latest["STOCH_D"]
            if k < 20 and k > d:
                comment_map["ストキャス（%K）"] = f"買い｜%K={k:.2f} > %D={d:.2f}"
            elif k > 80 and k < d:
                comment_map["ストキャス（%K）"] = f"売り｜%K={k:.2f} < %D={d:.2f}"
            else:
                trend = "横ばい"
                comment_map["ストキャス（%K）"] = f"中立｜%K={k:.2f}（{trend}中）"

        if "STOCH_D" in latest and "STOCH_D" in previous:
            d_val, prev_d_val = latest["STOCH_D"], previous["STOCH_D"]
            diff = d_val - prev_d_val
            trend = "上昇" if diff > 0 else "低下"
            if d_val > 80:
                comment_map["ストキャス（%D）"] = f"売り｜%D={d_val:.2f}（{trend}中）"
            elif d_val < 20:
                comment_map["ストキャス（%D）"] = f"買い｜%D={d_val:.2f}（{trend}中）"
            else:
                comment_map["ストキャス（%D）"] = f"中立｜%D={d_val:.2f}（{trend}中）"

        # ✅ ボリンジャーバンド
        if all(k in latest for k in ["Close", "BB_High", "BB_Low", "BB_MAVG"]):
            close = latest["Close"]
            bb_high = latest["BB_High"]
            bb_low = latest["BB_Low"]
            bb_mid = latest["BB_MAVG"]
            band_width = bb_high - bb_low
            diff_from_mid = close - bb_mid

            if close > bb_high:
                comment_map["BB上限"] = f"売り｜株価（終値）={close:.2f} > BB上限{bb_high:.2f}（買われすぎ）"
            elif close < bb_low:
                comment_map["BB下限"] = f"買い｜株価（終値）={close:.2f} < BB下限{bb_low:.2f}（売られすぎ）"
            else:
                deviation = (close - (bb_high + bb_low) / 2) / band_width * 100
                comment_map["BB中央"] = f"中立｜乖離={diff_from_mid:+.2f}円（終値={close:.2f} ）"

  ######### 指標判断-END- #########

        # ✅ テーブル_表示処理
        styled_table = []
        for row in table_data:
            label = row[0]
            comment = comment_map.get(label, "")
            styled_row = row + [emphasize(comment)]
            styled_table.append(styled_row)

        # ✅ テーブル_見栄え設定
        from IPython.display import HTML

        df_table = pd.DataFrame(styled_table, columns=["指標"] + date_labels + ["コメント"])

        styler = df_table.style.set_properties(**{'text-align': 'right'})
        styler = styler.set_properties(subset=["コメント"], **{'text-align': 'left'})
        styler = styler.set_table_styles([
            {"selector": "table", "props": [("border-collapse", "collapse"), ("border", "0px solid #ccc")]},
            {"selector": "th", "props": [("border", "1px solid #ccc"), ("background-color", "#f0f0f0"), ("text-align", "center")]},
            {"selector": "td", "props": [("border", "1px solid #ccc"), ("padding", "4px")]}
        ])

        # ✅ 総合シグナル評価（先に計算してから表示）
        buy_signals = sum("買い" in c for c in comment_map.values())
        sell_signals = sum("売り" in c for c in comment_map.values())
        if buy_signals > sell_signals:
            overall = "🔼 買い優勢"
        elif sell_signals > buy_signals:
            overall = "🔽 売り優勢"
        else:
            overall = "⏸ 中立・様子見"

        # ✅ collapseを強制適用する！
        styler = styler.set_table_attributes('style="border-collapse: collapse; border: 1px solid #ccc;"')

        # ✅ full_html を定義（←これも必須！）
        full_html = f"""
        <h4>{name}（{symbol}）｜取得日: {today_str}</h4>
        <p><b>✅ 総合シグナル：</b> {overall}（買い: {buy_signals}｜売り: {sell_signals}）</p>
        {styler.to_html(escape=False)}
        """

        # ✅ テーブル_表示（escape=False で絵文字も表示）
        from IPython.display import HTML

        #display(HTML(styler.to_html(escape=False)))
        display(HTML(full_html))
        display(Image(chart_path))
        #display(HTML(f'<img src="{chart_path}" style="width: 80%;">'))

        #comment_map = get_signal_comment(latest, previous)
        #score = float(comment_map["✅ 総合評価"].split("スコア:")[-1])
        #interpret_comment_map(comment_map, score)

        # ファイル保存設定
        from PIL import Image as PILImage

        def save_combined_chart_and_table(chart_path, html_table, output_dir, symbol, name, today_str,
                                          table_image_path="table_temp.jpg", save_pdf=False):
            """
            表（HTML）とチャート画像を結合し、JPGと必要に応じてPDFとして保存。
            """
            # ✅ HTML→画像化（テーブル）
            with open("temp_table.html", "w", encoding="utf-8") as f:
                f.write(html_table)

            config = imgkit.config(wkhtmltoimage='/usr/bin/wkhtmltoimage')
            options = {
                'format': 'jpg',
                'encoding': "UTF-8",
                'custom-header': [('Accept-Encoding', 'gzip')],
                'quality': '85',
                'zoom': 2,
                'crop-w': 1600
            }
            imgkit.from_file("temp_table.html", table_image_path, config=config, options=options)

            # ✅ 画像読み込み・結合
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
            combined_img.paste(table_img, (0, 0))
            combined_img.paste(chart_img, (0, table_img.height))

            # ✅ 保存先フォルダとファイル名
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
                rgb_img = combined_img.convert("RGB")  # PDFはRGB必要
                rgb_img.save(pdf_path, "PDF", resolution=100.0)
                print(f"📄 PDFとしても保存しました：{pdf_path}")

        if SHOW_SAVE_CHART:
          output_dir = "/content/drive/MyDrive/ColabNotebooks/銘柄分析"
          # PDFが不要なら「save_pdf=False」にする
          save_combined_chart_and_table(chart_path, full_html, output_dir, symbol, name, today_str, save_pdf=True)

######### 3.テーブル-END- #########

    except Exception as e:
        print(f"❌ エラー: {symbol} - {e}")

######### ループ-END- #########
