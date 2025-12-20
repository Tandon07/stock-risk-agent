import numpy as np

def compute_risk_score(context: dict):
    """
    context: dictionary from planner (price_data, fundamentals, sentiment, etc.)
    Returns: dict with risk_score, confidence, classification, reasons
    """
    risk_score = 0.0
    reasons = []

    # Extract safely
    price = context.get("price_data", {})
    fund = context.get("fundamentals", {})
    sent = context.get("sentiment", {})
    beta = fund.get("beta", 1.0)
    sentiment_val = sent.get("sentiment", 0.0)

    # --- Technical Risk (max 0.4)
    if price.get("RSI", 0) > 70:
        risk_score += 0.15
        reasons.append("RSI > 70 (overbought)")
    if price.get("MACD", 0) < 0:
        risk_score += 0.10
        reasons.append("MACD < 0 (bearish)")
    if price.get("EMA10", 0) < price.get("EMA50", 0):
        risk_score += 0.10
        reasons.append("EMA10 < EMA50 (short-term weakness)")
    if price.get("ATR", 0) > 5:  # arbitrary volatility threshold
        risk_score += 0.05
        reasons.append("ATR high (volatility warning)")

    # --- Sentiment Risk (max 0.3)
    if sentiment_val < 0:
        risk_score += 0.15
        reasons.append("Negative market/news sentiment")
    if any(a["sentiment"] == "NEGATIVE" for a in sent.get("articles", [])):
        risk_score += 0.15
        reasons.append("Recent negative headlines")

    # --- Fundamental Risk (max 0.2)
    pe = fund.get("PE_ratio")
    eps = fund.get("EPS")
    if pe and pe > 30:
        risk_score += 0.10
        reasons.append(f"PE ratio high ({pe:.1f})")
    if eps and eps < 0:
        risk_score += 0.10
        reasons.append("Negative EPS (loss-making)")

    # --- Market correlation / Beta (max 0.1)
    if beta and beta > 1.2:
        risk_score += 0.05
        reasons.append(f"High beta ({beta:.2f}) — sensitive to market moves")

    # clamp
    risk_score = min(risk_score, 1.0)

    # --- Confidence (based on volatility)
    avg_return = abs(price.get("EMA10", 0) - price.get("EMA50", 0))
    std_dev = price.get("ATR", 1)
    confidence = 1 - min(std_dev / (avg_return + 1e-5), 1.0)
    confidence = round(max(0.0, min(confidence, 1.0)), 2)

    # --- Risk classification
    if risk_score < 0.4:
        risk_class = "Low"
    elif risk_score <= 0.7:
        risk_class = "Medium"
    else:
        risk_class = "High"
        # -----------------------
    # DEBUG PRINT (no logic change)
    # -----------------------
    print("\n===== RISK SCORE INPUTS =====")

    print("\n--- PRICE DATA ---")
    print(f"RSI: {price.get('RSI')}")
    print(f"MACD: {price.get('MACD')}")
    print(f"EMA10: {price.get('EMA10')}")
    print(f"EMA50: {price.get('EMA50')}")
    print(f"ATR: {price.get('ATR')}")

    print("\n--- FUNDAMENTALS ---")
    print(f"Beta: {beta}")
    print(f"PE Ratio: {fund.get('PE_ratio')}")
    print(f"EPS: {fund.get('EPS')}")

    print("\n--- SENTIMENT ---")
    print(f"Sentiment Score: {sentiment_val}")
    print(f"Articles: {len(sent.get('articles', []))}")

    print("\n--- OUTPUT ---")
    print(f"Risk Score: {round(risk_score, 2)}")
    print(f"Confidence: {confidence}")
    print(f"Classification: {risk_class}")
    print(f"Reasons: {reasons}")

    print("==============================\n")

    return {
        "risk_score": round(risk_score, 2),
        "confidence": confidence,
        "classification": risk_class,
        "reasons": reasons
    }
