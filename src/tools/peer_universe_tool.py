from tools.screener import run_screener

def get_peer_universe(sector: str, market_cap: int) -> list[str]:
    """
    Get candidate peers from same sector & market cap band
    """
    if not sector or not market_cap:
        return []

    if market_cap > 2e12:
        cap_band = "large"
    elif market_cap > 5e11:
        cap_band = "mid"
    else:
        cap_band = "small"

    slots = {
        "intent": "stock_screener",
        "sector": sector,
        "market_cap_band": cap_band
    }

    results = run_screener(slots)

    return [r["ticker"].replace(".NS", "").replace(".BO", "") for r in results]
