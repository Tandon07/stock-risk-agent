import yfinance as yf

COMMODITY_MAP = {
    # 🟡 Precious Metals (MCX)
    "gold": "GOLD",
    "silver": "SILVER",

    # 🔩 Base Metals (MCX)
    "copper": "COPPER",
    "aluminium": "ALUMINIUM",
    "aluminum": "ALUMINIUM",   # alias
    "zinc": "ZINC",
    "lead": "LEAD",
    "nickel": "NICKEL",

    # 🛢 Energy (MCX)
    "crude oil": "CRUDEOIL",
    "oil": "CRUDEOIL",         # alias
    "natural gas": "NATGAS",
    "gas": "NATGAS",           # alias

    # 🌾 Agri (MCX)
    "cotton": "COTTON",
    "kapas": "KAPAS",

    # 🌾 Agri (NCDEX)
    "soybean": "SOYBEAN",
    "soy oil": "SOYOIL",
    "crude palm oil": "CPO",
    "mustard": "MUSTARD",
    "mustard seed": "MUSTARD",
    "refined soya oil": "REFSOYOIL",
    "castor seed": "CASTORSEED",
    "cotton seed oilcake": "CSO",
    "chana": "CHANA",
    "turmeric": "TURMERIC",
    "jeera": "JEERA",
    "dhaniya": "DHANIYA",
    "sugar": "SUGAR",
    "wheat": "WHEAT",
    "paddy": "PADDY",
    "maize": "MAIZE",
    "barley": "BARLEY",
}


def get_commodity_price(commodity: str):
    symbol = COMMODITY_MAP.get(commodity.lower())
    if not symbol:
        raise ValueError("Unsupported commodity")

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1mo")

    if hist.empty:
        raise ValueError("No price data")

    current_price = round(hist["Close"].iloc[-1], 2)
    prev_price = round(hist["Close"].iloc[-2], 2)

    pct_change = round(
        ((current_price - prev_price) / prev_price) * 100, 2
    )

    return {
        "symbol": symbol,
        "current_price": current_price,
        "prev_close": prev_price,
        "daily_change_pct": pct_change,
        "last_30d_high": round(hist["High"].max(), 2),
        "last_30d_low": round(hist["Low"].min(), 2),
    }