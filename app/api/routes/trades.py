from fastapi import APIRouter
from api.models.trade import Trade

router = APIRouter()

@router.get("/")
async def get_trades():
    trades = [
        Trade(symbol="AAPL", action="BUY", reason="Strong fundamentals"),
        Trade(symbol="TSLA", action="SELL", reason="Overvalued at current P/E"),
        Trade(symbol="MSFT", action="HOLD", reason="Stable growth expected"),
    ]
    return trades
