# src/advisor/advisor_reasoner.py
import json
from nlu.llm_client import LLMClient
from loguru import logger


def intent_guidance(intent: str, language: str):
    if language == "hi":
        if intent == "price_trend":
            return (
                "User trend जानना चाहता है। साफ़ शब्दों में बताइए कि "
                "trend ऊपर, नीचे या sideways है और momentum कैसा है। "
                "कोई भविष्यवाणी न करें।"
            )
        if intent == "buy_decision":
            return (
                "User खरीद को लेकर सोच रहा है। "
                "संभावनाओं और जोखिमों को संतुलित रूप में समझाइए। "
                "सीधे Buy/Sell न कहें।"
            )
        if intent == "risk_analysis":
            return (
                "User जोखिम समझना चाहता है। "
                "मुख्य risk drivers को आसान भाषा में समझाइए।"
            )
    else:
        if intent == "price_trend":
            return (
                "The user wants to understand the current trend. "
                "Clearly state whether the trend is upward, downward, or sideways, "
                "based on momentum indicators. Avoid predictions."
            )
        if intent == "buy_decision":
            return (
                "The user is considering a buy. "
                "Explain conditions under which it may or may not make sense, "
                "without giving direct advice."
            )
        if intent == "risk_analysis":
            return (
                "The user wants to understand risk. "
                "Explain the key risk drivers in simple terms."
            )
    return ""


def generate_advisor_output(slots: dict, context: dict, analysis: dict, explanation: dict):
    """
    Use the Groq LLM (or any backend) to synthesize a final bilingual,
    cautious, explainable narrative combining all data layers.
    """
    language = slots.get("language", "en")
    client = LLMClient()

    # Compact the context for readability
    context_summary = {
        "price_data": context.get("price_data", {}),
        "fundamentals": context.get("fundamentals", {}),
        "sentiment": context.get("sentiment", {}),
        "risk_score": analysis["risk_score"],
        "classification": analysis["classification"],
        "confidence": analysis["confidence"]
    }
    user_query = slots.get("_user_query", "")
    intent = slots.get("intent", "risk_analysis")
    guidance = intent_guidance(intent, language)

    prompt = f"""
    You are a calm, human-like financial market assistant.
    You speak in {language}.

    The user asked:
    "{user_query}"

    Your task:
    - Respond in the SAME tone and style as the user
    - Directly answer what the user is trying to understand
    - Be analytical but conversational
    - NEVER give direct buy/sell advice

    {guidance}

    Structure your response like this:
    1. Direct answer to the user’s question (trend / risk / outlook)
    2. Key indicators behind this view (RSI, MACD, sentiment, valuation)
    3. What this means practically *right now*
    4. One clear caution or condition to watch
    5. Considering all parameters give a decision (buy/sell) according to the user's query

    Data Summary (JSON):
    {json.dumps(context_summary, indent=2, ensure_ascii=False)}

    Risk classification: {analysis['classification']} ({analysis['risk_score']})
    Confidence level: {analysis['confidence']}
    Key risk reasons: {', '.join(analysis.get('reasons', []))}

    End with:
    "⚠️ This is a data-based analytical insight, not financial advice."
    """

    try:
        response = client.complete(prompt, temperature=0.3)
    except Exception as e:
        logger.error(f"Advisor LLM failed: {e}")
        response = explanation["text"]  # fallback to rule-based text

    return {
        "advisor_text": response.strip(),
        "advisor_json": {
            "slots": slots,
            "risk": analysis,
            "language": language,
            "explanation_text": explanation["text"],
            "advisor_output": response.strip()
        }
    }

def generate_comparison_output(context, language="en"):
    client = LLMClient()

    summary = []
    for r in context["results"]:
        summary.append({
            "stock": r["stock_name"],
            "risk_score": r["risk"]["risk_score"],
            "classification": r["risk"]["classification"],
            "confidence": r["risk"]["confidence"],
            "reasons": r["risk"].get("reasons", [])
        })

    prompt = f"""
You are a market analyst speaking in {language}.

The user asked to compare stocks.
Analyze them side-by-side and explain:

- Which stock looks more stable right now
- Which has higher risk or volatility
- What kind of investor each stock may suit

Do NOT give buy/sell advice.

Comparison Data (JSON):
{json.dumps(summary, indent=2, ensure_ascii=False)}

End with:
"⚠️ This is a data-based analytical insight, not financial advice."
"""

    return client.complete(prompt, temperature=0.3)

def generate_stock_news_output(context, language="en"):
    client = LLMClient()

    prompt = f"""
You are a market intelligence assistant speaking in {language}.

The user wants to understand recent discussions and sentiment.

Stock: {context}

Social Media Data (last 7 days):
Twitter posts:
{context}

Reddit discussions:
{context}

Your task:
- Summarize key discussion themes
- Describe overall sentiment (positive / neutral / negative)
- Highlight one potential concern and one positive point
- Keep it conversational and easy to understand

Do NOT give investment advice.

End with:
"⚠️ This reflects social sentiment and discussions, not financial advice."
"""

    return client.complete(prompt, temperature=0.3)

def generate_competitor_analysis_output(context, language="en"):
    client = LLMClient()

    summary = []
    for c in context["competitors"]:
        summary.append({
            "stock": c["stock_name"],
            "risk_score": c["risk"]["risk_score"],
            "classification": c["risk"]["classification"],
            "confidence": c["risk"]["confidence"],
            "reasons": c["risk"].get("reasons", [])
        })

    prompt = f"""
You are a market intelligence assistant speaking in {language}.

The user wants to understand how competitors of {context['base_stock']} 
are performing relative to each other.

Based on the data below:
- Identify which competitors look more stable
- Identify which look more volatile or risky
- Explain differences in simple, human language
- Do NOT give buy/sell advice

Competitor Data (JSON):
{json.dumps(summary, indent=2, ensure_ascii=False)}

Structure:
1. Overall peer-group snapshot
2. 1–2 relatively stable names
3. 1–2 higher-risk or volatile names
4. One clear takeaway for the user

End with:
"⚠️ This is a data-based analytical insight, not financial advice."
"""

    return client.complete(prompt, temperature=0.3)


def generate_sector_screener_output(user_input, context, language="en"):
    client = LLMClient()

    prompt = f"""
You are a market analyst speaking in {language}.

The user asked for stocks in the {context['sector']} sector.
Based on the user query answer it from the given context below.


Context:
{context['results']}

User Query: {user_input}

End with:
"⚠️ This is a data-based analytical insight, not financial advice."
"""
    return client.complete(prompt, temperature=0.3)


def generate_sector_trend_output(context, language="en"):
    client = LLMClient()

    prompt = f"""
You are a market intelligence assistant speaking in {language}.

The user wants to understand how the {context['sector']} sector
is performing currently.

Data:
Average risk score: {context['avg_risk']}
Overall trend: {context['trend']}

Explain:
- What this trend means
- How investors are reacting
- One caution to watch

End with:
"⚠️ This is a data-based analytical insight, not financial advice."
"""
    return client.complete(prompt, temperature=0.3)


def generate_commodity_trend_output(context, language="en"):
    price = context["price_data"]
    sentiment = context["sentiment"]

    prompt = f"""
You are a market analyst.

Commodity: {context['commodity']}

Current price: {price['current_price']}
Daily change: {price['daily_change_pct']}%
30-day range: {price['last_30d_low']} – {price['last_30d_high']}

Sentiment score: {sentiment.get('score')}

Explain the trend using:
- Price direction
- Volatility
- Sentiment alignment

Do NOT give financial advice.
Respond in {language}.
End with a disclaimer.
"""

    return LLMClient().complete(prompt, temperature=0.2)



def generate_commodity_news_output(context, language="en"):
    commodity = context["commodity"]
    news = context["news"]

    prompt = f"""
Summarize recent news and discussions about "{commodity}" in {language}.
Focus on macro factors, supply-demand, geopolitics.

News data:
{news}

End with:
⚠️ Informational summary only, not financial advice.
"""
    client = LLMClient()
    return client.complete(prompt, temperature=0.3)


from nlu.llm_client import LLMClient

def generate_info_general_output(context, language="en"):
    search_results = context["search_results"]


    return search_results

def generate_portfolio_guidance_output(context, language="en"):
    search_results = context["search_results"]

    return search_results
