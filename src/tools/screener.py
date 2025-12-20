# src/tools/screener.py

from tools.price_tool import get_price_data
from tools.fundamentals_tool import get_fundamentals
from risk.risk_engine import compute_risk_score

# Basic list (you can expand later)
WATCHLIST = [
    "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "RELIANCE.NS",
    "HINDUNILVR.NS", "ITC.NS", "LT.NS", "SBIN.NS", "AXISBANK.NS"
]

def run_screener(slots):
    target = slots.get("target_return_pct")
    horizon = slots.get("investment_horizon")
    sector = slots.get("sector")

    candidates = []

    for ticker in WATCHLIST:
        try:
            price = get_price_data(ticker)
            fundamentals = get_fundamentals(ticker)

            ctx = {
                "ticker": ticker,
                "price_data": price,
                "fundamentals": fundamentals,
                "sentiment": {"sentiment": 0, "articles": []}  # keep light for now
            }

            risk = compute_risk_score(ctx)
            candidates.append({"ticker": ticker, "risk": risk})

        except Exception:
            continue

    # sort by lowest risk
    ranked = sorted(candidates, key=lambda x: x["risk"]["risk_score"])

    # keep top 5 safest
    return ranked[:5]
