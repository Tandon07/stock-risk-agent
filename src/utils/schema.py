from pydantic import BaseModel
from typing import Optional, Union, List


class SlotFrame(BaseModel):
    intent: Optional[str]

    # Can be single stock or list (for comparison)
    stock_name: Optional[Union[str, List[str]]]

    # For commodities like gold, silver, oil, etc.
    commodity: Optional[str]

    ticker: Optional[str]
    capital: Optional[float]
    target_return_pct: Optional[float]
    investment_horizon: Optional[str]
    investor_type: Optional[str]
    risk_tolerance: Optional[str]
    sector: Optional[str]
    language: Optional[str]
    action: Optional[str]

    query_text: Optional[str]


# ==================================================
# ✅ INTENT → MANDATORY SLOTS MAP
# ==================================================
INTENT_MANDATORY_SLOTS = {
    # --- Stock single ---
    "risk_analysis": ["intent", "language", "stock_name"],
    "price_trend": ["intent", "language", "stock_name"],
    "buy_decision": ["intent", "language", "stock_name"],
    "sell_decision": ["intent", "language", "stock_name"],
    "stock_news": ["intent", "language", "stock_name"],

    # --- Multi-stock ---
    "stock_comparison": ["intent", "language", "stock_name"],
    "competitor_analysis": ["intent", "language", "stock_name"],

    # --- Screeners / Sectors ---
    "stock_screener": ["intent", "language"],
    "sector_screener": ["intent", "language", "sector"],
    "sector_trend": ["intent", "language", "sector"],

    # --- Portfolio ---
    "portfolio_guidance": ["intent", "language", "capital"],

    # --- Commodities ---
    "commodity_trend": ["intent", "language", "commodity"],
    "commodity_news": ["intent", "language", "commodity"],

    # --- General info (web search) ---
    "info_general": ["intent", "language", "query_text"],
}


# ==================================================
# ✅ FIND MISSING SLOTS BASED ON INTENT
# ==================================================
def find_missing_mandatory(slots: dict):
    intent = slots.get("intent")

    if not intent:
        return ["intent"]

    required = INTENT_MANDATORY_SLOTS.get(intent, ["intent", "language"])

    missing = []
    for k in required:
        val = slots.get(k)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(k)

    return missing
