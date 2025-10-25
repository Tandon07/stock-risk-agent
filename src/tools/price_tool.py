import yfinance as yf
import pandas_ta as ta
import pandas as pd

def get_price_data(ticker: str, period="6mo", interval="1d"):
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No price data for {ticker}")
    df["RSI"] = ta.rsi(df["Close"], length=14)
    macd = ta.macd(df["Close"])
    df["MACD"] = macd["MACD_12_26_9"]
    df["EMA10"] = ta.ema(df["Close"], length=10)
    df["EMA50"] = ta.ema(df["Close"], length=50)
    df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    return df.tail(1).to_dict("records")[0]   # latest indicators
# print(get_price_data(ticker="INFY.NS"))
