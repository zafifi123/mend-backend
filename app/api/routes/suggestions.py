from fastapi import APIRouter
from api.models import TradeSuggestion

router = APIRouter()

@router.get("/suggestions/{symbol}", response_model=list[TradeSuggestion])
def fetch_trade_suggestions(symbol: str):
    return [
        TradeSuggestion(symbol='AAPL', recommendation='Buy', score=0.91),
        TradeSuggestion(symbol='MSFT', recommendation='Hold', score=0.75),
        TradeSuggestion(symbol='TSLA', recommendation='Sell', score=0.35),
    ] 