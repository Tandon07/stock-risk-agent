SLOT_EXTRACTION_PROMPT = """
You are an AI assistant that extracts structured information (slots) from user queries 
related to stock market analysis.

Return ONLY valid JSON. No explanations.

The allowed intents are:
- "risk_analysis"
- "buy_decision"
- "sell_decision"
- "price_trend"
- "stock_screener"
- "stock_comparision"
- "portfolio_guidance"
- "competitor_analysis"
- "sector_trend"
- "sector_screener"

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

Use intent = "stock_comparison" when:
- The user mentions 2 or more stocks
- Uses words like "or", "vs", "compare", "which is better"

Use intent "portfolio_guidance" when:
- User mentions capital or amount of money
- User does NOT mention a specific stock
- User asks what to consider, where to invest, or how to invest

Use intent "stock_news" when:
- User asks about news, updates, headlines, announcements
- Phrases like "news", "updates", "what's going on", "latest"
- A specific stock or company is mentioned

Use intent "competitor_analysis" when:
- User asks about competitors, peers, rivals
- Phrases like:
  "competitors of X"
  "peers of X"
  "compared to peers"
  "how is X vs its competitors"
- User asks about competitors, peers, alternatives
- Mentions phrases like "competitors", "peers", "alternatives", "others doing"

Use intent "sector_screener" when:
- User asks for stocks in a sector
- Phrases like "list", "suggest", "best stocks" + sector name

Use intent "sector_trend" when:
- User asks how a sector is doing currently
- Phrases like "how is", "performance", "doing these days" + sector



The JSON schema you must produce:

{{
  "intent": "...",
  "stock_name": "string OR list of strings OR null"
  "ticker": null,
  "capital": float or null,
  "target_return_pct": float or null,
  "investment_horizon": "short_term | medium_term | long_term | null",
  "investor_type": "conservative | moderate | aggressive | null",
  "risk_tolerance": "low | medium | high | null",
  "sector": "string | null",
  "language": "en | hi",
  "action": "buy | sell | hold | unknown"
}}

Now extract the slots from this query:
"{query}"
"""
