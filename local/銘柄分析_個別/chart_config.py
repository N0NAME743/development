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

def judge_dynamic_zones(latest):
    """
    RSIとADXに基づいて、押し目ゾーン（low〜high）と利確ゾーン（profit_target）を自動で決定する関数。
    """
    rsi = latest["RSI"]
    adx = latest["ADX"]
    ma25 = latest["MA25"]
    ma75 = latest["MA75"]
    close = latest["Close"]

    # ✅ 最初にデフォルト値を明示しておく（これが重要！）
    oshime_low = ma75 * 0.95
    oshime_high = ma75
    profit_target = close * 1.03

    if adx > 25:
        if rsi < 50:
            # トレンド強く、まだ買われ過ぎでない → 押し目チャンス
            oshime_low = ma25 * 0.97
            oshime_high = ma25
        elif rsi > 70:
            # トレンド強いが過熱 → 利確重視
            profit_target = close * 0.98  # 手前で利確
    elif adx < 15:
        # トレンドが弱い → レンジ。深い押し目狙い
        oshime_low = ma75 * 0.93
        oshime_high = ma75 * 0.98

    return oshime_low, oshime_high, profit_target

def generate_zone_comment(close, profit_target, oshime_low, oshime_high, rsi, adx, trend):
    # 状況別コメントロジック
    if close >= profit_target:
        if rsi > 70:
            comment = (
                f"The current price is within the profit-taking zone, and the RSI is {rsi:.1f}, "
                f"indicating an overbought condition. Full profit-taking should be considered."
            )
            color = "#cc0000"  # 濃い赤（全利確）
        else:
            comment = (
                f"The price has reached the profit-taking zone (from {profit_target:.1f} JPY), "
                f"but the RSI is {rsi:.1f}, suggesting moderate momentum. Partial profit-taking may be appropriate."
            )
            color = "#f4c2c2"  # 淡い赤（部分利確）

    elif oshime_low <= close <= oshime_high:
        if rsi < 50 and adx > 25:
            comment = (
                f"The price is approaching the pullback zone ({oshime_low:.1f}–{oshime_high:.1f} JPY). "
                f"RSI: {rsi:.1f}, ADX: {adx:.1f}. This indicates a strong uptrend undergoing a temporary correction. "
                f"A rebound is worth monitoring."
            )
            color = "#006400"  # 濃い緑（全力買い）
        else:
            comment = (
                f"The price is within the pullback zone, but RSI is {rsi:.1f} and ADX is {adx:.1f}, "
                f"suggesting a weaker trend. Entry should be made with caution."
            )
            color = "#b2d8b2"  # 淡い緑（打診買い）

    else:
        comment = (
            f"The price is currently outside the defined zones. "
            f"Consider taking a cautious approach to both entries and exits."
        )
        color = "#d3d3d3"  # グレー（中立ゾーン）

    return comment, color

def plot_chart(df, symbol, name):

    rcParams['font.family'] = ['MS Gothic', 'Meiryo', 'Arial Unicode MS']  # ✅ Windows向けフォント

    recent_days = 60
    df_recent = df.tail(recent_days).copy()

    latest = df_recent.iloc[-1]

    if latest["MA5"] > latest["MA25"] > latest["MA75"]:
        trend_text = "UP"
    elif latest["MA5"] < latest["MA25"] < latest["MA75"]:
        trend_text = "DOWN"
    else:
        trend_text = "SIDEWAY"

    # ✅ 動的ゾーンを取得（関数呼び出し）
    oshime_low, oshime_high, profit_target = judge_dynamic_zones(latest)
 
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
        #title = f"{name} ({symbol}) {recent_days} DaysChart/Trend: {trend_text}",
        title="",  # 🔁 ここを空に
        ylabel="Price",
        volume=True,
        figscale=1.5,
        returnfig=True
    )

    fig.subplots_adjust(left=0.08, right=0.92)

    # 📝 タイトル & コメントを手動で追加
    fig.suptitle(
        f"{name} ({symbol}) {recent_days} DaysChart / Trend: {trend_text}",
        fontsize=12,
        fontweight='bold',
        ha='center',
        x=0.55,
        y=0.98
    )

    zone_comment, comment_color = generate_zone_comment(
        close=latest["Close"],
        profit_target=profit_target,
        oshime_low=oshime_low,
        oshime_high=oshime_high,
        rsi=latest["RSI"],
        adx=latest["ADX"],
        trend=trend_text
    )

    fig.text(
        0.55, 0.92,
        zone_comment,
        ha='center',
        fontsize=9,
        wrap=True,
        bbox=dict(
            facecolor=comment_color,
            edgecolor='gray',
            boxstyle='round,pad=0.3',
            alpha=0.6
        )
    )

    ax_main = axes[0]

    x = range(len(df_recent))
    # 押し目ゾーン（緑）
    ax_main.fill_between(
        x, oshime_low, oshime_high,
        where=[True] * len(df_recent),
        facecolor='green', alpha=0.15, label='押し目ゾーン'
    )
    # 利確ゾーン（オレンジ）
    ax_main.fill_between(
        x, profit_target, df_recent["High"].max(),
        where=[True] * len(df_recent),
        facecolor='orange', alpha=0.15, label='利確ゾーン'
    )

    # ✅ 押し目マーカー表示（緑の●）
    oshime_condition = (
        (df_recent["RSI"] > 40) & (df_recent["RSI"] < 55) &
        (df_recent["Close"] >= df_recent["MA25"] * 0.97) & (df_recent["Close"] <= df_recent["MA25"])
    )
    for idx in df_recent[oshime_condition].index:
        x_pos = df_recent.index.get_loc(idx)
        y_val = df_recent.loc[idx, "Low"]
        ax_main.plot(x_pos, y_val, marker='o', color='green', markersize=6, zorder=5)

    # ✅ 売りときマーカー表示（赤い✕）
    uri_condition = (
        (df_recent["RSI"] >= 70) &
        (df_recent["Close"] >= profit_target)
    )

    for idx in df_recent[uri_condition].index:
        x_pos = df_recent.index.get_loc(idx)
        y_val = df_recent.loc[idx, "High"]
        ax_main.plot(x_pos, y_val, marker='x', color='red', markersize=7, linewidth=2, zorder=6)

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
    #file_name = f"chart_{symbol}_{today_str}.png"
    file_name = f"chart_{symbol}_{name}_{today_str}.png"
    save_path = os.path.join(folder_name, file_name)

    # 💾 保存
    fig.savefig(save_path)
    #print(f"📈 Saved with MA, S/R lines, and Ichimoku Cloud (filled): {save_path}")
    print(f"📈 {save_path}")
    plt.close(fig)  # ✅ メモリリーク防止

    return save_path  # ✅ ← この行を追加！
