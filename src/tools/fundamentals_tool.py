import yfinance as yf

def get_fundamentals(ticker: str):
    t = yf.Ticker(ticker)
    info = t.info
    return {
        "PE_ratio": info.get("trailingPE"),
        "EPS": info.get("trailingEps"),
        "sector": info.get("sector"),
        "beta": info.get("beta")
    }
# print(get_fundamentals(ticker="INFY.NS"))