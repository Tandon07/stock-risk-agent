from tools.price_tool import get_price_data
from risk.risk_engine import compute_risk_score

def analyze_portfolio(portfolio: dict):
    """
    portfolio = {
      "positions": [
        {
          "stock": "Infosys",
          "ticker": "INFY.NS",
          "quantity": 10,
          "buy_price": 1200,
          "buy_date": "2024-01-10"
        }
      ]
    }
    """

    results = []
    total_value = 0.0

    # First pass: compute values
    for pos in portfolio["positions"]:
        ticker = pos["ticker"]
        qty = pos["quantity"]
        buy_price = pos["buy_price"]

        price_data = get_price_data(ticker)

        # price_data is a dict (latest candle)
        current_price = float(price_data["Close"])

        current_value = current_price * qty
        invested_value = buy_price * qty
        pnl = current_value - invested_value
        pnl_pct = (pnl / invested_value) * 100 if invested_value else 0.0

        context = {
            "stock": pos["stock"],
            "ticker": ticker,
            "price_data": price_data,
            "fundamentals": {},   # you can plug real fundamentals later
            "sentiment": {}       # and real sentiment later
        }

        risk = compute_risk_score(context)

        results.append({
            "stock": pos["stock"],
            "ticker": ticker,
            "quantity": qty,
            "buy_price": buy_price,
            "current_price": round(current_price, 2),
            "invested_value": round(invested_value, 2),
            "current_value": round(current_value, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "risk": risk,
            "technicals": {
                "RSI": price_data.get("RSI"),
                "MACD": price_data.get("MACD"),
                "EMA10": price_data.get("EMA10"),
                "EMA50": price_data.get("EMA50"),
                "ATR": price_data.get("ATR"),
            }
        })

        total_value += current_value

    # Second pass: compute weights
    for r in results:
        r["weight_pct"] = round((r["current_value"] / total_value) * 100, 2) if total_value else 0.0

    return {
        "total_value": round(total_value, 2),
        "positions": results
    }
