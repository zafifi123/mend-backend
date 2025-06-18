def score_trade(features: dict) -> float:
    volatility = features.get("volatility", 0.5)
    trend_strength = features.get("trend_strength", 0.5)
    return 1 - (0.6 * trend_strength - 0.4 * volatility)
