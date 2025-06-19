from fastapi import APIRouter
from api.models import MarketInsight

router = APIRouter()

@router.get("/", response_model=MarketInsight)
def get_market_insights():
    return MarketInsight(
        sentiment='Bullish',
        topSectors=['Technology', 'Healthcare'],
        volatilityAlert='Increased volatility expected this week due to earnings season and Fed announcements.'
    ) 