import json

def explain_result(stock_name: str, analysis: dict, context: dict, language="en"):
    """
    Generate human-readable explanation text.
    """
    risk = analysis["risk_score"]
    conf = analysis["confidence"]
    cls = analysis["classification"]
    reasons = analysis["reasons"]

    # Simplify reason list
    summary = "; ".join(reasons[:3]) if reasons else "Stable indicators overall."

    if language == "hi":
        text = (
            f"{stock_name} का जोखिम स्तर **{cls} ({risk})** है। "
            f"विश्वास स्तर: {conf}। मुख्य कारण: {summary}। "
            "⚠️ यह डेटा आधारित विश्लेषण है, निवेश सलाह नहीं।"
        )
    else:
        text = (
            f"{stock_name} shows a **{cls} risk ({risk})** with confidence {conf}. "
            f"Key indicators: {summary}. "
            "⚠️ This is a data-based analytical insight, not financial advice."
        )

    return {
        "text": text,
        "json": {
            "stock_name": stock_name,
            "risk_score": risk,
            "confidence": conf,
            "classification": cls,
            "reasons": reasons,
            "sources": ["Yahoo Finance", "NewsAPI", "FinBERT"],
            "disclaimer": "⚠️ This is a data-based analytical insight, not financial advice."
        }
    }
