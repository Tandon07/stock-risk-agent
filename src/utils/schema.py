from pydantic import BaseModel, Field
from typing import Optional

class SlotFrame(BaseModel):
    intent: str = Field(..., description="risk_analysis | buy_decision | sell_decision | price_trend | advice_general")
    stock_name: Optional[str] = None
    ticker: Optional[str] = None
    capital: Optional[float] = None
    target_return_pct: Optional[float] = None
    investment_horizon: Optional[str] = None
    investor_type: Optional[str] = None
    risk_tolerance: Optional[str] = None
    sector: Optional[str] = None
    language: str = Field(..., description="en | hi")
    action: Optional[str] = None

MANDATORY_SLOTS = ["stock_name", "intent", "language"]

def find_missing_mandatory(slots: dict):
    return [k for k in MANDATORY_SLOTS if not slots.get(k)]
