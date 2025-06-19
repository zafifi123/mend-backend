from typing import Dict, List, Any
from temporalio import activity
import numpy as np
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from temporal.models import CombinedRecommendation
from api.core.db import get_conn

@activity.defn
async def combine_recommendations(
    ml_recommendations: List[Any],
    llama_recommendations: List[Any]
) -> List[CombinedRecommendation]:
    """Combine ML and Llama recommendations using ensemble methods."""
    
    # Create lookup dictionaries
    ml_lookup = {rec.symbol: rec for rec in ml_recommendations}
    llama_lookup = {rec.symbol: rec for rec in llama_recommendations}
    
    # Get all unique symbols
    all_symbols = set(ml_lookup.keys()) | set(llama_lookup.keys())
    
    combined_recommendations = []
    
    for symbol in all_symbols:
        ml_rec = ml_lookup.get(symbol)
        llama_rec = llama_lookup.get(symbol)
        
        if ml_rec and llama_rec:
            # Both analyses available - combine them
            combined = combine_two_analyses(symbol, ml_rec, llama_rec)
        elif ml_rec:
            # Only ML analysis available
            combined = convert_to_combined(ml_rec, "ML")
        elif llama_rec:
            # Only Llama analysis available
            combined = convert_to_combined(llama_rec, "Llama")
        else:
            continue
        
        combined_recommendations.append(combined)
    
    # Apply ensemble ranking
    ranked_recommendations = apply_ensemble_ranking(combined_recommendations)
    
    return ranked_recommendations

def combine_two_analyses(symbol: str, ml_rec: Any, llama_rec: Any) -> CombinedRecommendation:
    """Combine ML and Llama analyses for the same symbol."""
    
    # Weight the analyses (you can adjust these weights)
    ml_weight = 0.6
    llama_weight = 0.4
    
    # Calculate weighted confidence
    weighted_confidence = (ml_rec.confidence * ml_weight + llama_rec.confidence * llama_weight)
    
    # Determine consensus action
    action = determine_consensus_action(ml_rec.action, llama_rec.action, ml_rec.confidence, llama_rec.confidence)
    
    # Combine reasoning
    reasoning = combine_reasoning(ml_rec.reasoning, llama_rec.reasoning)
    
    # Determine risk level (take the higher risk level)
    risk_level = determine_higher_risk(ml_rec.risk_level, llama_rec.risk_level)
    
    # Determine timeframe (take the shorter timeframe for more actionable recommendations)
    timeframe = determine_shorter_timeframe(ml_rec.timeframe, llama_rec.timeframe)
    
    # Calculate price targets (weighted average)
    price_target = (ml_rec.price_target * ml_weight + llama_rec.price_target * llama_weight)
    stop_loss = (ml_rec.stop_loss * ml_weight + llama_rec.stop_loss * llama_weight)
    
    # Calculate consensus score
    consensus_score = calculate_consensus_score(ml_rec, llama_rec)
    
    return CombinedRecommendation(
        symbol=symbol,
        action=action,
        confidence=weighted_confidence,
        reasoning=reasoning,
        risk_level=risk_level,
        timeframe=timeframe,
        price_target=price_target,
        stop_loss=stop_loss,
        ml_confidence=ml_rec.confidence,
        llama_confidence=llama_rec.confidence,
        consensus_score=consensus_score
    )

def determine_consensus_action(ml_action: str, llama_action: str, ml_conf: float, llama_conf: float) -> str:
    """Determine the consensus action between ML and Llama."""
    
    if ml_action == llama_action:
        return ml_action
    
    # If actions differ, use confidence-weighted decision
    if ml_conf > llama_conf:
        return ml_action
    else:
        return llama_action

def combine_reasoning(ml_reasoning: str, llama_reasoning: str) -> str:
    """Combine reasoning from both analyses."""
    
    combined = f"ML Analysis: {ml_reasoning[:150]}... "
    combined += f"Llama Analysis: {llama_reasoning[:150]}..."
    
    return combined

def determine_higher_risk(ml_risk: str, llama_risk: str) -> str:
    """Determine the higher risk level between two analyses."""
    
    risk_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    
    ml_risk_score = risk_levels.get(ml_risk, 2)
    llama_risk_score = risk_levels.get(llama_risk, 2)
    
    max_risk_score = max(ml_risk_score, llama_risk_score)
    
    for risk, score in risk_levels.items():
        if score == max_risk_score:
            return risk
    
    return "MEDIUM"

def determine_shorter_timeframe(ml_timeframe: str, llama_timeframe: str) -> str:
    """Determine the shorter timeframe between two analyses."""
    
    timeframe_days = {
        "1-3 days": 2,
        "3-7 days": 5,
        "1-2 weeks": 10.5
    }
    
    ml_days = timeframe_days.get(ml_timeframe, 5)
    llama_days = timeframe_days.get(llama_timeframe, 5)
    
    min_days = min(ml_days, llama_days)
    
    for timeframe, days in timeframe_days.items():
        if days == min_days:
            return timeframe
    
    return "3-7 days"

def calculate_consensus_score(ml_rec: Any, llama_rec: Any) -> float:
    """Calculate a consensus score based on agreement and confidence."""
    
    # Base score is average confidence
    base_score = (ml_rec.confidence + llama_rec.confidence) / 2
    
    # Bonus for action agreement
    if ml_rec.action == llama_rec.action:
        agreement_bonus = 0.1
    else:
        agreement_bonus = 0.0
    
    # Bonus for high confidence in both analyses
    if ml_rec.confidence > 0.8 and llama_rec.confidence > 0.8:
        confidence_bonus = 0.1
    else:
        confidence_bonus = 0.0
    
    return min(1.0, base_score + agreement_bonus + confidence_bonus)

def convert_to_combined(rec: Any, source: str) -> CombinedRecommendation:
    """Convert a single analysis to combined format."""
    
    return CombinedRecommendation(
        symbol=rec.symbol,
        action=rec.action,
        confidence=rec.confidence,
        reasoning=f"{source} Analysis: {rec.reasoning}",
        risk_level=rec.risk_level,
        timeframe=rec.timeframe,
        price_target=rec.price_target,
        stop_loss=rec.stop_loss,
        ml_confidence=rec.confidence if source == "ML" else 0.0,
        llama_confidence=rec.confidence if source == "Llama" else 0.0,
        consensus_score=rec.confidence * 0.8  # Lower score for single analysis
    )

def apply_ensemble_ranking(recommendations: List[CombinedRecommendation]) -> List[CombinedRecommendation]:
    """Apply ensemble ranking to sort recommendations."""
    
    # Calculate ensemble scores
    for rec in recommendations:
        # Multi-factor scoring
        ensemble_score = calculate_ensemble_score(rec)
        rec.confidence = ensemble_score
    
    # Sort by ensemble score
    recommendations.sort(key=lambda x: x.confidence, reverse=True)
    
    return recommendations

def calculate_ensemble_score(rec: CombinedRecommendation) -> float:
    """Calculate ensemble score using multiple factors."""
    
    # Base score (consensus score)
    base_score = rec.consensus_score
    
    # Factor 1: Action preference (BUY > HOLD > SELL for most traders)
    action_scores = {"BUY": 1.0, "HOLD": 0.7, "SELL": 0.8}
    action_score = action_scores.get(rec.action, 0.7)
    
    # Factor 2: Risk-adjusted return potential
    risk_scores = {"LOW": 1.0, "MEDIUM": 0.9, "HIGH": 0.7}
    risk_score = risk_scores.get(rec.risk_level, 0.8)
    
    # Factor 3: Timeframe preference (shorter timeframes preferred)
    timeframe_scores = {"1-3 days": 1.0, "3-7 days": 0.9, "1-2 weeks": 0.8}
    timeframe_score = timeframe_scores.get(rec.timeframe, 0.8)
    
    # Factor 4: Confidence consistency
    confidence_consistency = 1.0 - abs(rec.ml_confidence - rec.llama_confidence)
    
    # Weighted ensemble score
    ensemble_score = (
        base_score * 0.4 +
        action_score * 0.2 +
        risk_score * 0.15 +
        timeframe_score * 0.15 +
        confidence_consistency * 0.1
    )
    
    return min(1.0, ensemble_score)

@activity.defn
async def store_recommendations(recommendations: List[CombinedRecommendation]) -> Dict[str, Any]:
    """Store recommendations in the database."""
    
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    from api.core.db import get_conn
    
    stored_count = 0
    for rec in recommendations:
        try:
            # Use the same database connection as the API
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Insert recommendation into database
                    insert_query = """
                    INSERT INTO recommendations (
                        symbol, action, confidence, reasoning, risk_level, timeframe,
                        price_target, stop_loss, ml_confidence, llama_confidence, consensus_score
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cur.execute(insert_query, (
                        rec.symbol,
                        rec.action,
                        rec.confidence,
                        rec.reasoning,
                        rec.risk_level,
                        rec.timeframe,
                        rec.price_target,
                        rec.stop_loss,
                        rec.ml_confidence,
                        rec.llama_confidence,
                        rec.consensus_score
                    ))
                    
                    conn.commit()
                    stored_count += 1
                    print(f"Stored recommendation for {rec.symbol}: {rec.action} (confidence: {rec.confidence:.2f})")
            
        except Exception as e:
            print(f"Error storing recommendation for {rec.symbol}: {e}")
            continue
    
    return {
        "status": "success",
        "stored_count": stored_count,
        "total_count": len(recommendations),
        "timestamp": datetime.now().isoformat()
    } 