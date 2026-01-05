import yfinance as yf

def get_company_profile(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "marketCap": info.get("marketCap"),
        "shortName": info.get("shortName")
    }

# print(get_company_profile("Eternal.NS"))