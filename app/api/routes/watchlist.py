from fastapi import APIRouter, Depends
from api.core.db import get_conn
from api.models import WatchlistItem
import yfinance as yf
from pydantic import BaseModel

router = APIRouter()

class SymbolIn(BaseModel):
    symbol: str

@router.get("/", response_model=list[WatchlistItem])
def get_watchlist(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT symbol FROM watchlist")
        rows = cur.fetchall()
        items = []
        for row in rows:
            symbol = row[0]
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get("regularMarketPrice", 0.0)
            change = info.get("regularMarketChangePercent", 0.0)
            volume = info.get("volume", 0)
            marketCap = info.get("marketCap", "")
            sector = info.get("sector", "")
            name = info.get("shortName", symbol)
            # Format change as a string with percent
            change_str = f"{change:+.2f}%" if isinstance(change, float) else str(change)
            marketCap_str = f"{marketCap:,}" if isinstance(marketCap, int) else str(marketCap)
            items.append(WatchlistItem(
                symbol=symbol,
                name=name,
                price=price,
                change=change_str,
                volume=volume,
                marketCap=marketCap_str,
                sector=sector
            ))
        return items

@router.post("/")
def add_to_watchlist(data: SymbolIn, conn=Depends(get_conn)):
    symbol = data.symbol
    with conn.cursor() as cur:
        cur.execute("INSERT INTO watchlist (symbol) VALUES (%s)", (symbol,))
        conn.commit()
    return {"success": True}

@router.put("/{symbol}")
def update_watchlist_item(symbol: str, item: dict, conn=Depends(get_conn)):
    # No extra fields to update in this schema, so just return success
    return {"success": True, "symbol": symbol, "updated": item}

@router.delete("/{symbol}")
def remove_from_watchlist(symbol: str, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM watchlist WHERE symbol = %s", (symbol,))
        conn.commit()
    return {"success": True} 