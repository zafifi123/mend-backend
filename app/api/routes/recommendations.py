from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.database import get_db_connection
from pydantic import BaseModel

router = APIRouter()

class RecommendationResponse(BaseModel):
    symbol: str
    action: str
    confidence: float
    reasoning: str
    risk_level: str
    timeframe: str
    price_target: float
    stop_loss: float
    ml_confidence: float
    llama_confidence: float
    consensus_score: float
    created_at: datetime

@router.get("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(limit: Optional[int] = 5):
    """Get the latest trading recommendations."""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get the latest recommendations
                query = """
                SELECT 
                    symbol,
                    action,
                    confidence,
                    reasoning,
                    risk_level,
                    timeframe,
                    price_target,
                    stop_loss,
                    ml_confidence,
                    llama_confidence,
                    consensus_score,
                    created_at
                FROM recommendations 
                WHERE created_at >= %s
                ORDER BY consensus_score DESC, created_at DESC
                LIMIT %s
                """
                
                # Get recommendations from the last 24 hours
                yesterday = datetime.now() - timedelta(days=1)
                
                cur.execute(query, (yesterday, limit))
                recommendations = cur.fetchall()
                
                if not recommendations:
                    # If no recent recommendations, return empty list
                    return []
                
                return [RecommendationResponse(**rec) for rec in recommendations]
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/recommendations/{symbol}", response_model=List[RecommendationResponse])
async def get_recommendations_by_symbol(symbol: str, limit: Optional[int] = 3):
    """Get recommendations for a specific symbol."""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                SELECT 
                    symbol,
                    action,
                    confidence,
                    reasoning,
                    risk_level,
                    timeframe,
                    price_target,
                    stop_loss,
                    ml_confidence,
                    llama_confidence,
                    consensus_score,
                    created_at
                FROM recommendations 
                WHERE symbol = %s AND created_at >= %s
                ORDER BY created_at DESC
                LIMIT %s
                """
                
                # Get recommendations from the last 7 days for the symbol
                week_ago = datetime.now() - timedelta(days=7)
                
                cur.execute(query, (symbol.upper(), week_ago, limit))
                recommendations = cur.fetchall()
                
                if not recommendations:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"No recent recommendations found for {symbol}"
                    )
                
                return [RecommendationResponse(**rec) for rec in recommendations]
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/recommendations/stats")
async def get_recommendation_stats():
    """Get statistics about recommendations."""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get overall stats
                stats_query = """
                SELECT 
                    COUNT(*) as total_recommendations,
                    COUNT(CASE WHEN action = 'BUY' THEN 1 END) as buy_count,
                    COUNT(CASE WHEN action = 'SELL' THEN 1 END) as sell_count,
                    COUNT(CASE WHEN action = 'HOLD' THEN 1 END) as hold_count,
                    AVG(confidence) as avg_confidence,
                    AVG(consensus_score) as avg_consensus_score,
                    MAX(created_at) as latest_recommendation
                FROM recommendations 
                WHERE created_at >= %s
                """
                
                # Stats from last 7 days
                week_ago = datetime.now() - timedelta(days=7)
                
                cur.execute(stats_query, (week_ago,))
                stats = cur.fetchone()
                
                # Get top performing symbols
                top_symbols_query = """
                SELECT 
                    symbol,
                    COUNT(*) as recommendation_count,
                    AVG(confidence) as avg_confidence,
                    AVG(consensus_score) as avg_consensus_score
                FROM recommendations 
                WHERE created_at >= %s
                GROUP BY symbol
                ORDER BY avg_consensus_score DESC
                LIMIT 5
                """
                
                cur.execute(top_symbols_query, (week_ago,))
                top_symbols = cur.fetchall()
                
                return {
                    "overall_stats": dict(stats),
                    "top_symbols": [dict(symbol) for symbol in top_symbols],
                    "period": "7 days"
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/recommendations/refresh")
async def trigger_recommendation_refresh():
    """Manually trigger a recommendation refresh (for testing)."""
    
    try:
        # This would typically call the Temporal workflow
        # For now, we'll just return a success message
        return {
            "status": "success",
            "message": "Recommendation refresh triggered",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering refresh: {str(e)}") 