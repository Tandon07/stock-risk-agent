from tools.price_tool import get_price_data
from tools.fundamentals_tool import get_fundamentals
from risk.risk_engine import compute_risk_score
from tools.ticker_resolver import resolve_ticker
from tools.news_tool import get_sentiment
from tools.rag_tool import get_static_context
from tools.screener import run_screener
from tools.competitor_search_tool import search_competitors
from tools.sector_search_tool import search_sector_stocks


def plan_and_retrieve(slots: dict):
    intent = slots.get("intent")
    language = slots.get("language", "en")


    # ==================================================
    # 2️⃣ PORTFOLIO GUIDANCE (capital-based, no ticker)
    # ==================================================
    if intent == "portfolio_guidance":
        return {
            "mode": "portfolio_guidance",
            "capital": slots.get("capital"),
            "language": language
        }

    # ==================================================
    # 3️⃣ STOCK COMPARISON (MULTIPLE STOCKS)
    # ==================================================
    if intent == "stock_comparison":
        stock_names = slots.get("stock_name")

        if not isinstance(stock_names, list) or len(stock_names) < 2:
            return {"error": "At least two stocks are required for comparison"}

        results = []

        for stock in stock_names:
            resolver = resolve_ticker(stock)
            if not resolver:
                continue

            # Prefer NSE over BSE
            if resolver.get("NSE"):
                ticker = resolver["NSE"] + ".NS"
            elif resolver.get("BSE"):
                ticker = resolver["BSE"] + ".BO"
            else:
                continue

            try:
                price_data = get_price_data(ticker)
                fundamentals = get_fundamentals(ticker)
                sentiment = get_sentiment(stock)
                static_ctx = get_static_context(stock)
            except Exception:
                continue

            # 🔑 Build per-stock context
            stock_context = {
                "stock": stock,
                "ticker": ticker,
                "price_data": price_data,
                "fundamentals": fundamentals,
                "sentiment": sentiment,
                "rag_context": static_ctx
            }

            # 🔑 COMPUTE RISK HERE
            risk = compute_risk_score(stock_context)

            results.append({
                "stock_name": stock,
                "ticker": ticker,
                "risk": risk,
                "context": stock_context
            })

        if len(results) < 2:
            return {"error": "Insufficient data for stock comparison"}

        return {
            "mode": "stock_comparison",
            "results": results,
            "language": language
        }


    # ==================================================
    # 4️⃣ STOCK NEWS (Twitter + Reddit)
    # ==================================================
    if intent == "stock_news":
        stock_name = slots.get("stock_name")

        if not stock_name:
            return {"error": "Stock name required for news"}

        from tools.social_news_tool import get_social_news

        try:
            social_news = get_social_news(stock_name)
        except Exception as e:
            return {"error": str(e)}

        return {
            "mode": "stock_news",
            "stock": stock_name,
            "social_news": social_news,
            "language": language
        }


    # ==================================================
    # 5️⃣ COMPETITOR ANALYSIS (DYNAMIC)
    # ==================================================
    if intent == "competitor_analysis":
        stock_name = slots.get("stock_name")
        language = slots.get("language", "en")

        if not stock_name:
            return {"error": "Stock name required for competitor analysis"}

        try:
            competitors = search_competitors(stock_name)
        except Exception as e:
            return {"error": f"Competitor search failed: {e}"}

        results = []

        for comp in competitors:
            resolver = resolve_ticker(comp)
            if not resolver:
                continue

            if resolver.get("NSE"):
                ticker = resolver["NSE"] + ".NS"
            elif resolver.get("BSE"):
                ticker = resolver["BSE"] + ".BO"
            else:
                continue

            try:
                price_data = get_price_data(ticker)
                fundamentals = get_fundamentals(ticker)
                sentiment = get_sentiment(comp)
            except Exception:
                continue

            comp_context = {
                "stock": comp,
                "ticker": ticker,
                "price_data": price_data,
                "fundamentals": fundamentals,
                "sentiment": sentiment
            }

            risk = compute_risk_score(comp_context)

            results.append({
                "stock_name": comp,
                "ticker": ticker,
                "risk": risk
            })

        if not results:
            return {"error": "No competitor data available"}

        return {
            "mode": "competitor_analysis",
            "base_stock": stock_name,
            "competitors": results,
            "language": language
        }

    # ==================================================
    # SECTOR SCREENER
    # ==================================================
    if intent == "sector_screener":
        sector = slots.get("sector")
        language = slots.get("language", "en")

        if not sector:
            return {"error": "Sector name required"}

        stocks = search_sector_stocks(sector)
        print("Stocks in agent_panner",stocks)
        results = []

        # # for name in stocks:
        # #     resolver = resolve_ticker(name)
        # #     if not resolver:
        # #         continue

        # #     if resolver.get("NSE"):
        # #         ticker = resolver["NSE"] + ".NS"
        # #     elif resolver.get("BSE"):
        # #         ticker = resolver["BSE"] + ".BO"
        # #     else:
        # #         continue

        # #     try:
        # #         price_data = get_price_data(ticker)
        # #         fundamentals = get_fundamentals(ticker)
        # #         sentiment = get_sentiment(name)
        # #     except Exception:
        # #         continue

        # #     ctx = {
        # #         "stock": name,
        # #         "ticker": ticker,
        # #         "price_data": price_data,
        # #         "fundamentals": fundamentals,
        # #         "sentiment": sentiment
        # #     }

        # #     risk = compute_risk_score(ctx)

        #     results.append({
        #         "stock_name": name,
        #         "ticker": ticker,
        #         "risk": risk
        #     })

        # if not results:
        #     return {"error": "No sector data available"}

        # # Rank by lowest risk
        # results = sorted(results, key=lambda x: x["risk"]["risk_score"])

        return {
            "mode": "sector_screener",
            "sector": sector,
            # "results": results[:5],
            "results": stocks,
            "language": language
        }

    # ==================================================
    # SECTOR TREND (CURRENT STATE)
    # ==================================================
    if intent == "sector_trend":
        sector = slots.get("sector")
        language = slots.get("language", "en")

        if not sector:
            return {"error": "Sector name required"}

        stocks = search_sector_stocks(sector)
        aggregate = []

        for name in stocks:
            resolver = resolve_ticker(name)
            if not resolver:
                continue

            if resolver.get("NSE"):
                ticker = resolver["NSE"] + ".NS"
            elif resolver.get("BSE"):
                ticker = resolver["BSE"] + ".BO"
            else:
                continue

            try:
                price_data = get_price_data(ticker)
                fundamentals = get_fundamentals(ticker)
                sentiment = get_sentiment(name)
            except Exception:
                continue

            ctx = {
                "stock": name,
                "ticker": ticker,
                "price_data": price_data,
                "fundamentals": fundamentals,
                "sentiment": sentiment
            }

            risk = compute_risk_score(ctx)
            aggregate.append(risk["risk_score"])

        if not aggregate:
            return {"error": "Insufficient data for sector trend"}

        avg_risk = sum(aggregate) / len(aggregate)

        if avg_risk < 0.4:
            trend = "Relatively Stable"
        elif avg_risk < 0.7:
            trend = "Moderate Volatility"
        else:
            trend = "High Volatility"

        return {
            "mode": "sector_trend",
            "sector": sector,
            "avg_risk":     round(avg_risk, 2),
            "trend": trend,
            "language": language
        }

    # ==================================================
    # 5️⃣ SINGLE STOCK MODES (trend, risk, buy_decision)
    # ==================================================
    stock_name = slots.get("stock_name")

    if not stock_name:
        return {"error": "No stock specified"}

    resolver = resolve_ticker(stock_name)

    if not resolver:
        return {"error": f"Ticker not found for {stock_name}"}

    # Prefer NSE over BSE
    if resolver.get("NSE"):
        ticker = resolver["NSE"] + ".NS"
    elif resolver.get("BSE"):
        ticker = resolver["BSE"] + ".BO"
    else:
        return {"error": f"Ticker not found for {stock_name}"}

    context = {
        "stock": stock_name,
        "ticker": ticker,
        "intent": intent,
        "language": language
    }

    try:
        price_data = get_price_data(ticker)
        fundamentals = get_fundamentals(ticker)
        sentiment = get_sentiment(stock_name)
        static_ctx = get_static_context(stock_name)
    except Exception as e:
        return {"error": str(e)}

    context.update({
        "price_data": price_data,
        "fundamentals": fundamentals,
        "sentiment": sentiment,
        "rag_context": static_ctx
    })
    return context