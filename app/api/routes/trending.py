from fastapi import APIRouter, Depends
from api.core.db import get_conn
from api.models import TrendingStock, TopMover
from api.core.cache import get_tickers_info

router = APIRouter()

def enrich_trending_with_av(row):
    symbol = row[1]
    tickers_info = get_tickers_info([symbol])
    info = tickers_info.get(symbol, {})
    name = info.get("shortName", row[2])
    return TrendingStock(symbol=symbol, name=name)

def enrich_mover_with_av(row):
    symbol = row[1]
    tickers_info = get_tickers_info([symbol])
    info = tickers_info.get(symbol, {})
    name = info.get("shortName", row[2])
    change = info.get("regularMarketChangePercent", 0.0)
    change_str = f"{change:+.2f}%" if isinstance(change, float) else str(change)
    return TopMover(symbol=symbol, name=name, change=change_str)

@router.get("/trending", response_model=list[TrendingStock])
def get_trending_stocks(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM trending_stocks")
        rows = cur.fetchall()
        return [enrich_trending_with_av(row) for row in rows]

@router.get("/movers", response_model=list[TopMover])
def get_top_movers(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM top_movers")
        rows = cur.fetchall()
        return [enrich_mover_with_av(row) for row in rows] 