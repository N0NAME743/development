# ==============================
# analyzer.py｜シグナル統合・注目度・コメント生成（完全版）
# ==============================

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, ADXIndicator

# ==========================
# 買いシグナル判定関数群
# ==========================

def detect_candlestick_patterns(df):
    patterns = []
    if df["Close"].iloc[-1] > df["Open"].iloc[-1] and df["Low"].iloc[-1] < df["Low"].rolling(3).min().iloc[-1]:
        patterns.append("下ヒゲ陽線（反発兆候）")
    return patterns

def detect_weekly_signals(df):
    signals = []
    if df["Close"].iloc[-1] > df["High"].rolling(5).max().iloc[-1]:
        signals.append("週足高値ブレイク")
    return signals

def detect_mid_term_golden_cross(df):
    signals = []
    ma25 = df["Close"].rolling(25).mean()
    ma75 = df["Close"].rolling(75).mean()
    if ma25.iloc[-2] < ma75.iloc[-2] and ma25.iloc[-1] > ma75.iloc[-1]:
        signals.append("中期ゴールデンクロス")
    return signals

def detect_pullback_bounce(df):
    signals = []
    ma25 = df["Close"].rolling(25).mean()
    if df["Close"].iloc[-2] > ma25.iloc[-2] and df["Close"].iloc[-1] > ma25.iloc[-1]:
        signals.append("押し目陽線")
    return signals

def detect_trendline_bounce(df):
    signals = []
    low_diff = df["Low"].diff()
    if low_diff.iloc[-3] > 0 and low_diff.iloc[-2] > 0 and low_diff.iloc[-1] > 0:
        signals.append("上昇トレンドライン反発")
    return signals

def detect_higher_lows(df):
    signals = []
    lows = df["Low"].rolling(3).min()
    if lows.iloc[-3] < lows.iloc[-2] < lows.iloc[-1]:
        signals.append("下値切り上げ継続")
    return signals

# ==========================
# 売りシグナル判定関数群（買いシグナルの反対）
# ==========================

def detect_rsi_fall(df):
    rsi = RSIIndicator(df["Close"]).rsi()
    if rsi.iloc[-2] > 70 and rsi.iloc[-1] < rsi.iloc[-2]:
        return ["RSI反落（過熱から下降）"]
    return []

def detect_mid_term_dead_cross(df):
    ma25 = df["Close"].rolling(25).mean()
    ma75 = df["Close"].rolling(75).mean()
    if ma25.iloc[-2] > ma75.iloc[-2] and ma25.iloc[-1] < ma75.iloc[-1]:
        return ["中期デッドクロス"]
    return []

def detect_recent_low_break(df):
    if df["Low"].iloc[-1] < df["Low"].iloc[-60:-1].min():
        return ["直近安値割れ"]
    return []

def detect_return_sell_signal(df):
    ma25 = df["Close"].rolling(25).mean()
    if df["Close"].iloc[-2] < ma25.iloc[-2] and df["Close"].iloc[-1] < ma25.iloc[-1]:
        return ["戻り売り陰線"]
    return []

def detect_trendline_break(df):
    low_diff = df["Low"].diff()
    if low_diff.iloc[-3] < 0 and low_diff.iloc[-2] < 0 and low_diff.iloc[-1] < 0:
        return ["下降トレンドライン割れ"]
    return []

def detect_lower_highs(df):
    highs = df["High"].rolling(3).max()
    if highs.iloc[-3] > highs.iloc[-2] > highs.iloc[-1]:
        return ["高値切り下げ継続"]
    return []

def detect_three_black_crows(df):
    close = df["Close"]
    open_ = df["Open"]
    if all(close.iloc[-i] < open_.iloc[-i] for i in range(1, 4)):
        return ["三連続陰線（弱気連続）"]
    return []

def detect_weekly_low_break(df):
    if df["Low"].iloc[-1] < df["Low"].rolling(5).min().iloc[-1]:
        return ["週足安値ブレイク"]
    return []

# ==========================

# analyzer.py の中などに追加
def evaluate_signal_strength(signals_dict: dict) -> int:
    score = 0

    # 加点ルール（買い）
    for sig in signals_dict.get("buy", []):
        if "ゴールデン" in sig or "直近高値" in sig:
            score += 3
        elif "反発" in sig or "押し目" in sig or "切り上げ" in sig:
            score += 2
        else:
            score += 1

    # 減点ルール（売り）
    for sig in signals_dict.get("sell", []):
        if "陰転" in sig or "三連続陰線" in sig or "デッドクロス" in sig:
            score -= 3
        elif "過熱" in sig or "戻り売り" in sig or "切り下げ" in sig:
            score -= 2
        else:
            score -= 1

    return score  # -10 〜 +10 のスコアを想定

def analyze_signals(signals: list[str], adx_last: float) -> tuple:
    signal_dict = classify_signals(signals)
    score = evaluate_signal_strength(signal_dict)

    # 内部スコアに基づく attention 判定
    if score >= 4:
        attention = "買い注目"
        comment = ":star: 買いシグナルが複数出現中"
    elif score <= -3:
        attention = "売り優勢"
        comment = ":warning: 売りシグナルが優勢です。調整に注意"
    elif score <= 1 and score >= -2:
        attention = "様子見"
        comment = "📊 シグナルが拮抗しています。判断に注意"
    else:
        attention = "様子見"
        comment = "中立圏です。シグナルは弱め"

    return attention, comment, score, str(score)

def analyze_stock(df, info=None):
    if len(df) < 30:
        return [], "ー", "", "中立（様子見）", 0, ""

    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    open_ = df["Open"]
    volume = df["Volume"]

    # テクニカル指標
    df["RSI"] = RSIIndicator(close, window=14).rsi()
    macd = MACD(close)
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    adx = ADXIndicator(high, low, close)
    df["ADX"] = adx.adx()

    signals = []

    # テクニカルシグナル
    if df["MACD"].iloc[-2] < df["MACD_signal"].iloc[-2] and df["MACD"].iloc[-1] > df["MACD_signal"].iloc[-1]:
        signals.append("MACD陽転")
    if df["MACD"].iloc[-2] > df["MACD_signal"].iloc[-2] and df["MACD"].iloc[-1] < df["MACD_signal"].iloc[-1]:
        signals.append("MACD陰転")
    if df["RSI"].iloc[-2] < 30 and df["RSI"].iloc[-1] > 30:
        signals.append("RSI反発")
    if df["RSI"].iloc[-2] < 70 and df["RSI"].iloc[-1] > 70:
        signals.append("RSI過熱")
    if df["Close"].iloc[-1] < df["Close"].rolling(window=25).mean().iloc[-1]:
        signals.append("移動平均線下抜け")
    if df["High"].iloc[-1] > df["High"].iloc[-60:-1].max():
        signals.append("直近高値突破")
    if df["High"].iloc[-1] >= df["High"].max():
        signals.append("期間内高値更新（要注目）")

    signals += detect_candlestick_patterns(df)
    signals += detect_danger_signals(df) if "detect_danger_signals" in globals() else []
    spike_flag = detect_spike_history(df)
    if spike_flag:
        signals.append(spike_flag)
    if info:
        signals += detect_risky_fundamentals(info)
    signals += detect_weekly_signals(df)
    signals += detect_mid_term_golden_cross(df)
    signals += detect_pullback_bounce(df)
    signals += detect_trendline_bounce(df)
    signals += detect_higher_lows(df)
    signals += detect_rsi_fall(df)
    signals += detect_mid_term_dead_cross(df)
    signals += detect_recent_low_break(df)
    signals += detect_return_sell_signal(df)
    signals += detect_trendline_break(df)
    signals += detect_lower_highs(df)
    signals += detect_three_black_crows(df)
    signals += detect_weekly_low_break(df)

    adx_last = df["ADX"].iloc[-1]
    attention, comment, score, score_str = analyze_signals(signals, adx_last)
    return signals, comment, "", attention, score, score_str

def classify_signals(signals: list[str]) -> dict:
    buy_keywords = ["陽転", "反発", "ゴールデン", "突破", "押し目", "切り上げ", "雲上抜け"]
    sell_keywords = [
        "陰転", "過熱", "下抜け", "赤字", "危険", "急騰", "利確", "調整", "雲下抜け",
        "デッドクロス", "安値割れ", "戻り売り", "下降トレンドライン", "切り下げ", "三連続陰線", "週足安値"
    ]

    result = {"buy": [], "sell": [], "neutral": []}
    for s in signals:
        if any(kw in s for kw in buy_keywords):
            result["buy"].append(s)
        elif any(kw in s for kw in sell_keywords):
            result["sell"].append(s)
        else:
            result["neutral"].append(s)
    return result

def detect_spike_history(df, threshold=0.4):
    change = (df["Close"] - df["Close"].shift(1)) / df["Close"].shift(1)
    if (change.abs() > threshold).sum() >= 1:
        return "過去に急騰／急落歴あり" #⚠️
    return None
