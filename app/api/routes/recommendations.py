from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from api.core.db import get_conn
from pydantic import BaseModel

router = APIRouter()

class RecommendationResponse(BaseModel):
    id: int
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
    """Get the latest trading recommendations not yet accepted by user 123."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('''
            SELECT * FROM recommendations r
            WHERE NOT EXISTS (
                SELECT 1 FROM trades t WHERE t.rec_id = r.id AND t.user_id = %s
            )
        ''', (123,))
        recommendations = cur.fetchall()
        items = [RecommendationResponse(**rec) for rec in recommendations]
        return items

class AcceptRecommendationRequest(BaseModel):
    rec_id: int
    user_id: int = 123

@router.post("/accept", response_model=dict)
async def accept_recommendation(req: AcceptRecommendationRequest, conn=Depends(get_conn)):
    """Accept a recommendation by inserting a trade with rec_id and user_id=123."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get recommendation details
        cur.execute("SELECT * FROM recommendations WHERE id = %s", (req.rec_id,))
        rec = cur.fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        # Insert trade with rec_id, using correct fields
        cur.execute(
            "INSERT INTO trades (user_id, symbol, action, price, status, rec_id, quantity) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (req.user_id, rec["symbol"], rec["action"], rec["price_target"], 'pending_allocation', req.rec_id, None)
        )
        trade_id = cur.fetchone()["id"]
        conn.commit()
    return {"success": True, "trade_id": trade_id}

