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
