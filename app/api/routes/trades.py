from fastapi import APIRouter, Depends, HTTPException
from api.core.db import get_conn
from api.models import TradeEnriched
import yfinance as yf

router = APIRouter()

def enrich_trade_with_yf(row):
    symbol = row[2]
    ticker = yf.Ticker(symbol)
    info = ticker.info
    price = info.get("regularMarketPrice", float(row[4]))
    change = info.get("regularMarketChangePercent", 0.0)
    volume = info.get("volume", 0)
    marketCap = info.get("marketCap", "")
    sector = info.get("sector", "")
    name = info.get("shortName", symbol)
    change_str = f"{change:+.2f}%" if isinstance(change, float) else str(change)
    marketCap_str = f"{marketCap:,}" if isinstance(marketCap, int) else str(marketCap)
    return TradeEnriched(
        symbol=symbol,
        action=row[3],
        reason="",
        price=price,
        quantity=row[5],
        status=row[6],
        executed_at=row[7],
        name=name,
        change=change_str,
        volume=volume,
        marketCap=marketCap_str,
        sector=sector
    )

@router.get("/history", response_model=list[TradeEnriched])
def get_trade_history(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM trades WHERE status = 'Completed'")
        rows = cur.fetchall()
        return [enrich_trade_with_yf(row) for row in rows]

@router.get("/active", response_model=list[TradeEnriched])
def get_active_trades(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM trades WHERE status = 'Active'")
        rows = cur.fetchall()
        return [enrich_trade_with_yf(row) for row in rows]

@router.get("/pending", response_model=list[TradeEnriched])
def get_pending_orders(conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM trades WHERE status = 'Pending'")
        rows = cur.fetchall()
        return [enrich_trade_with_yf(row) for row in rows]

@router.post("/")
def add_trade(trade: dict, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO trades (symbol, action, price, quantity, status, executed_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (trade["symbol"], trade["action"], trade["price"], trade["quantity"], trade.get("status", "Pending"), trade.get("executed_at"))
        )
        conn.commit()
    return {"success": True, "trade": trade}

@router.put("/{trade_id}")
def update_trade(trade_id: int, trade: dict, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM trades WHERE id = %s", (trade_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trade not found")
        for key, value in trade.items():
            cur.execute(f"UPDATE trades SET {key} = %s WHERE id = %s", (value, trade_id))
        conn.commit()
    return {"success": True, "trade_id": trade_id, "updated": trade}

@router.delete("/{trade_id}")
def delete_trade(trade_id: int, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM trades WHERE id = %s", (trade_id,))
        conn.commit()
    return {"success": True, "trade_id": trade_id}
