def decide_position_action(pos):
    tech = pos["technicals"]
    risk = pos["risk"]

    rsi = tech.get("RSI", 50)
    macd = tech.get("MACD", 0)
    ema10 = tech.get("EMA10", 0)
    ema50 = tech.get("EMA50", 0)
    atr = tech.get("ATR", 0)

    risk_score = risk["risk_score"]
    weight = pos["weight_pct"]
    pnl_pct = pos["pnl_pct"]
    current_price = pos["current_price"]

    # Trend phase detection
    if ema10 > ema50 and macd > 0:
        trend_phase = "Uptrend"
    elif ema10 < ema50 and macd < 0:
        trend_phase = "Downtrend"
    else:
        trend_phase = "Sideways"

    # Action logic
    if trend_phase == "Downtrend" and pnl_pct < -10:
        action = "REDUCE / EXIT"
        holding_horizon = "Short-term only (risk of further downside)"
    elif trend_phase == "Uptrend":
        action = "HOLD / ADD ON DIPS"
        holding_horizon = "Medium to Long-term"
    else:
        action = "HOLD / WATCH"
        holding_horizon = "Wait for confirmation"

    # Risk & concentration override
    if weight > 40:
        action = "TRIM POSITION"
    
    # Stop-loss suggestion (ATR based)
    stop_loss = round(current_price - 2 * atr, 2) if atr else None

    return {
        "action": action,
        "trend_phase": trend_phase,
        "holding_horizon": holding_horizon,
        "suggested_stop_loss": stop_loss,
        "risk_score": risk_score
    }
