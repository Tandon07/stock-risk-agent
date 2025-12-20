from tools.price_tool import get_price_data
from tools.fundamentals_tool import get_fundamentals
from tools.news_tool import get_sentiment
from tools.rag_tool import get_static_context
from tools.screener import run_screener
from tools.ticker_resolver import resolve_ticker


def plan_and_retrieve(slots: dict):
    intent = slots.get("intent")

    if intent == "stock_screener":
        suggestions = run_screener(slots)
        return {"mode": "screener", "suggestions": suggestions}

    stock = slots.get("stock_name")
    context = {"stock": stock, "intent": intent}

    stock_name = slots.get("stock_name")
    resolver = resolve_ticker(stock_name)
    ticker = resolver.get('NSE') if resolver.get('NSE') else resolver.get('BSE')

    if ticker is None:
        return {"error": f"Ticker not found for {stock_name}"}
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
