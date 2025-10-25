from tools.price_tool import get_price_data
from tools.fundamentals_tool import get_fundamentals
from tools.news_tool import get_sentiment
from tools.rag_tool import get_static_context

def plan_and_retrieve(slots: dict):
    intent = slots.get("intent")
    stock = slots.get("stock_name")
    context = {"stock": stock, "intent": intent}

    # Map stock name -> ticker (simplified)
    ticker_map = {"Infosys": "INFY.NS", "HDFC": "HDFCBANK.NS", "Reliance": "RELIANCE.NS"}
    ticker = ticker_map.get(stock, None)
    if not ticker:
        context["error"] = f"Ticker not found for {stock}"
        return context
    context["ticker"] = ticker

    try:
        price_data = get_price_data(ticker)
        fundamentals = get_fundamentals(ticker)
        sentiment = get_sentiment(stock)
        static_ctx = get_static_context(stock)
    except Exception as e:
        context["error"] = str(e)
        return context

    context.update({
        "price_data": price_data,
        "fundamentals": fundamentals,
        "sentiment": sentiment,
        "rag_context": static_ctx
    })
    return context
