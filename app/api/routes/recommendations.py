from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from api.core.db import get_conn
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

@router.get("/", response_model=List[RecommendationResponse])
async def get_recommendations(conn=Depends(get_conn)):
    """Get the latest trading recommendations."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('''
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
        ''')
        recommendations = cur.fetchall()
        items = [RecommendationResponse(**rec) for rec in recommendations]
        return items

