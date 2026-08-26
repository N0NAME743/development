# indicator_calc.py
import pandas as pd
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
from ta import momentum

def calculate_indicators(df, flags):
    # 強制的にSeriesへ変換
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()

    high = df["High"]
    if isinstance(high, pd.DataFrame):
        high = high.squeeze()

    low = df["Low"]
    if isinstance(low, pd.DataFrame):
        low = low.squeeze()

    volume = df["Volume"]
    if isinstance(volume, pd.DataFrame):
        volume = volume.squeeze()

    df["RSI"] = momentum.RSIIndicator(close, window=14).rsi()
    df["Vol_MA5"] = volume.rolling(5).mean()
    df["Vol_MA25"] = volume.rolling(25).mean()
    df["MA5"] = close.rolling(5).mean()
    df["MA25"] = close.rolling(25).mean()
    df["MA75"] = close.rolling(75).mean()
    df["MA200"] = close.rolling(200).mean()

    if flags.SHOW_MACD:
        macd = MACD(close)
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Diff"] = macd.macd_diff()
    if flags.SHOW_BB:
        bb = BollingerBands(close)
        df["BB_High"] = bb.bollinger_hband()
        df["BB_Low"] = bb.bollinger_lband()
        df["BB_MAVG"] = bb.bollinger_mavg()
    if flags.SHOW_ADX:
        adx = ADXIndicator(high, low, close)
        df["ADX"] = adx.adx()
    if flags.SHOW_STOCH:
        stoch = StochasticOscillator(high, low, close)
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()
    if flags.SHOW_MA_DEVIATION:
        df["MA25_Deviation"] = (close - df["MA25"]) / df["MA25"] * 100

    return df
