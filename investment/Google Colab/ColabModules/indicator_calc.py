# indicator_calc.py
import pandas as pd
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
from ta import momentum

def calculate_indicators(df, flags):
    df["RSI"] = momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["Vol_MA5"] = df["Volume"].rolling(5).mean()
    df["Vol_MA25"] = df["Volume"].rolling(25).mean()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA25"] = df["Close"].rolling(25).mean()
    df["MA75"] = df["Close"].rolling(75).mean()
    df["MA200"] = df["Close"].rolling(200).mean()

    if flags.SHOW_MACD:
        macd = MACD(df["Close"])
        df["MACD"] = macd.macd()
        df["MACD_Signal"] = macd.macd_signal()
        df["MACD_Diff"] = macd.macd_diff()
    if flags.SHOW_BB:
        bb = BollingerBands(df["Close"])
        df["BB_High"] = bb.bollinger_hband()
        df["BB_Low"] = bb.bollinger_lband()
        df["BB_MAVG"] = bb.bollinger_mavg()
    if flags.SHOW_ADX:
        adx = ADXIndicator(df["High"], df["Low"], df["Close"])
        df["ADX"] = adx.adx()
    if flags.SHOW_STOCH:
        stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()
    if flags.SHOW_MA_DEVIATION:
        df["MA25_Deviation"] = (df["Close"] - df["MA25"]) / df["MA25"] * 100

    return df
