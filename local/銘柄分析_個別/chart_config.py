import mplfinance as mpf
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, ADXIndicator
from ta.volatility import BollingerBands

def add_indicators(df):
    df["RSI"] = RSIIndicator(df["Close"]).rsi()
    df["MA25"] = df["Close"].rolling(25).mean()
    macd = MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    bb = BollingerBands(df["Close"])
    df["BB_High"] = bb.bollinger_hband()
    df["BB_Low"] = bb.bollinger_lband()
    adx = ADXIndicator(df["High"], df["Low"], df["Close"])
    df["ADX"] = adx.adx()
    stoch = StochasticOscillator(df["High"], df["Low"], df["Close"])
    df["STOCH_K"] = stoch.stoch()
    return df

def plot_chart(df, symbol, name):
    df_recent = df.tail(60).copy()
    addplots = [
        mpf.make_addplot(df_recent["MA25"], color="orange"),
        mpf.make_addplot(df_recent["RSI"], panel=1, color='blue'),
        mpf.make_addplot(df_recent["MACD"], panel=2, color='green'),
        mpf.make_addplot(df_recent["MACD_signal"], panel=2, color='red')
    ]
    save_path = f"chart_{symbol}.png"
    mpf.plot(
        df_recent,
        type='candle',
        style='yahoo',
        addplot=addplots,
        title=f"{name} ({symbol}) - 株価チャート",
        ylabel="株価",
        volume=True,
        savefig=save_path
    )
    print(f"📈 保存完了: {save_path}")
