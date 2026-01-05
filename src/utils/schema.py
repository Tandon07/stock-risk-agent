from pydantic import BaseModel
from typing import Optional, Union, List


class SlotFrame(BaseModel):
    intent: Optional[str]

    # 🔑 KEY CHANGE
    stock_name: Optional[Union[str, List[str]]]

    ticker: Optional[str]
    capital: Optional[float]
    target_return_pct: Optional[float]
    investment_horizon: Optional[str]
    investor_type: Optional[str]
    risk_tolerance: Optional[str]
    sector: Optional[str]
    language: Optional[str]
    action: Optional[str]


INTENT_MANDATORY_SLOTS = {
    "risk_analysis": ["intent", "language", "stock_name"],
    "price_trend": ["intent", "language", "stock_name"],
    "buy_decision": ["intent", "language", "stock_name"],
    "stock_news": ["intent", "language", "stock_name"],
    "stock_comparison": ["intent", "language", "stock_name"],
    "competitor_analysis": ["intent", "language", "stock_name"],
    "portfolio_guidance": ["intent", "language", "capital"],
    "sector_screener": ["intent", "language", "sector"],
    "sector_trend": ["intent", "language", "sector"],
}

def find_missing_mandatory(slots: dict):
    intent = slots.get("intent")
    if not intent:
        return ["intent"]

    required = INTENT_MANDATORY_SLOTS.get(intent, ["intent", "language"])
    return [k for k in required if not slots.get(k)]

