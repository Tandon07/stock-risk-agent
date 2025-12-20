SLOT_EXTRACTION_PROMPT = """
You are an AI assistant that extracts structured information (slots) from user queries 
related to stock market analysis.

Return ONLY valid JSON. No explanations.

The allowed intents are:
- "risk_analysis"
- "buy_decision"
- "sell_decision"
- "price_trend"
- "advice_general"
- "stock_screener"

Use "stock_screener" ONLY when:
- User asks for multiple stocks
- User asks “suggest”, “recommend”, “list”, “best stocks”
- User does NOT mention a specific company name

If the user mentions a specific stock name (even with return %),
DO NOT use stock_screener.

Examples:
- "about TCS for 10% return in a year" → intent = risk_analysis
- "Infosys current trend" → intent = price_trend
- "Suggest stocks for 10% return" → intent = stock_screener


The JSON schema you must produce:

{{
  "intent": "...",
  "stock_name": "string or null",
  "ticker": null,
  "capital": float or null,
  "target_return_pct": float or null,
  "investment_horizon": "short_term | medium_term | long_term | null",
  "investor_type": "conservative | moderate | aggressive | null",
  "risk_tolerance": "low | medium | high | null",
  "sector": "string or null",
  "language": "en | hi",
  "action": "buy | sell | hold | unknown"
}}

Now extract the slots from this query:
"{query}"
"""
