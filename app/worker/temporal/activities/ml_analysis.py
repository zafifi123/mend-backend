import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, List, Any
from temporalio import activity
from temporal.models import MLRecommendation

@activity.defn
async def run_ml_analysis(market_data: Dict[str, Any]) -> List[MLRecommendation]:
    """Run classical ML analysis on market data."""
    
    recommendations = []
    
    for symbol, data in market_data.items():
        try:
            # Extract features
            features = extract_features(data)
            
            # Generate recommendation using multiple ML approaches
            recommendation = analyze_stock_ml(symbol, features, data)
            
            if recommendation:
                recommendations.append(recommendation)
                
        except Exception as e:
            print(f"Error in ML analysis for {symbol}: {e}")
            continue
    
    # Sort by confidence and return top recommendations
    recommendations.sort(key=lambda x: x.confidence, reverse=True)
    return recommendations

def extract_features(data: Dict[str, Any]) -> Dict[str, float]:
    """Extract features for ML analysis."""
    tech = data.get('technical_indicators', {})
    
    features = {
        'rsi': tech.get('rsi', 50),
        'macd': tech.get('macd', 0),
        'price_vs_sma20': tech.get('price_vs_sma20', 0),
        'price_vs_sma50': tech.get('price_vs_sma50', 0),
        'volume': data.get('volume', 0),
        'pe_ratio': data.get('pe_ratio', 0),
        'beta': data.get('beta', 1),
        'market_cap': data.get('market_cap', 0),
        'bb_position': calculate_bb_position(tech),
        'volatility': calculate_volatility(data.get('historical_data', [])),
        'momentum': calculate_momentum(data.get('historical_data', [])),
        'sentiment_score': data.get('news_sentiment', {}).get('sentiment_score', 0)
    }
    
    return features

def calculate_bb_position(tech: Dict[str, float]) -> float:
    """Calculate position within Bollinger Bands."""
    if not all(k in tech for k in ['bb_upper', 'bb_middle', 'bb_lower']):
        return 0.5
    
    current_price = tech.get('bb_middle', 0)
    bb_range = tech['bb_upper'] - tech['bb_lower']
    
    if bb_range == 0:
        return 0.5
    
    position = (current_price - tech['bb_lower']) / bb_range
    return max(0, min(1, position))

def calculate_volatility(historical_data: List[Dict]) -> float:
    """Calculate price volatility."""
    if len(historical_data) < 2:
        return 0
    
    prices = [day['Close'] for day in historical_data]
    returns = np.diff(prices) / prices[:-1]
    return np.std(returns) * 100

def calculate_momentum(historical_data: List[Dict]) -> float:
    """Calculate price momentum."""
    if len(historical_data) < 5:
        return 0
    
    recent_prices = [day['Close'] for day in historical_data[-5:]]
    return (recent_prices[-1] / recent_prices[0] - 1) * 100

def analyze_stock_ml(symbol: str, features: Dict[str, float], data: Dict[str, Any]) -> MLRecommendation:
    """Analyze stock using classical ML approaches."""
    
    # Rule-based analysis
    action, confidence, reasoning = rule_based_analysis(features)
    
    # Statistical analysis
    stat_action, stat_confidence = statistical_analysis(features)
    
    # Combine analyses
    final_action = combine_analyses(action, stat_action, confidence, stat_confidence)
    final_confidence = (confidence + stat_confidence) / 2
    
    # Calculate price targets
    current_price = data.get('current_price', 0)
    price_target, stop_loss = calculate_price_targets(current_price, features, final_action)
    
    # Determine risk level
    risk_level = determine_risk_level(features, final_confidence)
    
    # Determine timeframe
    timeframe = determine_timeframe(features)
    
    return MLRecommendation(
        symbol=symbol,
        action=final_action,
        confidence=final_confidence,
        reasoning=reasoning,
        risk_level=risk_level,
        timeframe=timeframe,
        price_target=price_target,
        stop_loss=stop_loss
    )

def rule_based_analysis(features: Dict[str, float]) -> tuple:
    """Rule-based analysis using technical indicators."""
    rsi = features.get('rsi', 50)
    macd = features.get('macd', 0)
    price_vs_sma20 = features.get('price_vs_sma20', 0)
    bb_position = features.get('bb_position', 0.5)
    
    # RSI rules
    if rsi < 30:
        action = "BUY"
        confidence = 0.8
        reasoning = f"RSI oversold ({rsi:.1f})"
    elif rsi > 70:
        action = "SELL"
        confidence = 0.7
        reasoning = f"RSI overbought ({rsi:.1f})"
    else:
        action = "HOLD"
        confidence = 0.5
        reasoning = f"RSI neutral ({rsi:.1f})"
    
    # MACD confirmation
    if macd > 0 and action == "BUY":
        confidence += 0.1
        reasoning += ", MACD positive"
    elif macd < 0 and action == "SELL":
        confidence += 0.1
        reasoning += ", MACD negative"
    
    # Moving average confirmation
    if price_vs_sma20 > 2 and action == "BUY":
        confidence += 0.1
        reasoning += ", above SMA20"
    elif price_vs_sma20 < -2 and action == "SELL":
        confidence += 0.1
        reasoning += ", below SMA20"
    
    return action, min(0.95, confidence), reasoning

def statistical_analysis(features: Dict[str, float]) -> tuple:
    """Statistical analysis using historical patterns."""
    # Simplified statistical analysis
    # In a real implementation, you'd use trained models
    
    volatility = features.get('volatility', 0)
    momentum = features.get('momentum', 0)
    sentiment = features.get('sentiment_score', 0)
    
    # Momentum-based analysis
    if momentum > 5:
        action = "BUY"
        confidence = 0.7
    elif momentum < -5:
        action = "SELL"
        confidence = 0.7
    else:
        action = "HOLD"
        confidence = 0.6
    
    # Adjust confidence based on volatility
    if volatility > 20:
        confidence *= 0.8  # Reduce confidence for high volatility
    
    return action, confidence

def combine_analyses(action1: str, action2: str, conf1: float, conf2: float) -> str:
    """Combine multiple analyses."""
    if action1 == action2:
        return action1
    elif conf1 > conf2:
        return action1
    else:
        return action2

def calculate_price_targets(current_price: float, features: Dict[str, float], action: str) -> tuple:
    """Calculate price targets and stop loss."""
    volatility = features.get('volatility', 10)
    
    if action == "BUY":
        price_target = current_price * (1 + volatility / 100)
        stop_loss = current_price * (1 - volatility / 200)
    elif action == "SELL":
        price_target = current_price * (1 - volatility / 100)
        stop_loss = current_price * (1 + volatility / 200)
    else:
        price_target = current_price
        stop_loss = current_price * (1 - volatility / 200)
    
    return price_target, stop_loss

def determine_risk_level(features: Dict[str, float], confidence: float) -> str:
    """Determine risk level based on features."""
    volatility = features.get('volatility', 0)
    beta = features.get('beta', 1)
    
    if volatility > 25 or beta > 1.5:
        return "HIGH"
    elif volatility > 15 or beta > 1.2:
        return "MEDIUM"
    else:
        return "LOW"

def determine_timeframe(features: Dict[str, float]) -> str:
    """Determine recommended timeframe."""
    volatility = features.get('volatility', 0)
    
    if volatility > 20:
        return "1-3 days"
    elif volatility > 10:
        return "3-7 days"
    else:
        return "1-2 weeks" 