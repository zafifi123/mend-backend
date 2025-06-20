from fastapi import APIRouter, Depends, HTTPException, Query
from api.core.db import get_conn
from api.models import TradeEnriched
from api.core.cache import get_tickers_info
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

def enrich_trade(row, tickers_info):
    # trades table: id, user_id, symbol, action, price, quantity, status, executed_at, created_at
    symbol = str(row["symbol"])
    info = tickers_info.get(symbol, {})
    price = float(info.get("regularMarketPrice", float(row["price"])))
    change = info.get("regularMarketChangePercent", 0.0)
    volume = int(info.get("volume", 0))
    marketCap = info.get("marketCap", "")
    sector = info.get("sector", "")
    name = info.get("shortName", symbol)
    change_str = f"{change:+.2f}%" if isinstance(change, float) else str(change)
    marketCap_str = f"{marketCap:,}" if isinstance(marketCap, int) else str(marketCap)
    # Map and convert types for TradeEnriched
    return TradeEnriched(
        id=int(row["id"]),
        symbol=symbol,
        action=str(row["action"]),
        reason="",
        price=float(row["price"]),
        quantity=int(row["quantity"]) if row["quantity"] is not None else None,
        status=str(row["status"]),
        executed_at=row["executed_at"].isoformat() if row["executed_at"] else None,
        name=name,
        change=change_str,
        volume=volume,
        marketCap=marketCap_str,
        sector=sector
    )

@router.get("/", response_model=list[TradeEnriched])
def get_trades(conn=Depends(get_conn)):
    user_id = 123
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM trades WHERE user_id = %s", (user_id,))
        rows = cur.fetchall()
        symbols = list(set([row['symbol'] for row in rows]))
        tickers_info = get_tickers_info(symbols)
        return [enrich_trade(row, tickers_info) for row in rows]

@router.get("/active", response_model=list[TradeEnriched])
def get_active_trades(conn=Depends(get_conn)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM trades WHERE status = 'Active'")
        rows = cur.fetchall()
        symbols = list(set([row['symbol'] for row in rows]))
        tickers_info = get_tickers_info(symbols)
        return [enrich_trade(row, tickers_info) for row in rows]

@router.get("/pending", response_model=list[TradeEnriched])
def get_pending_orders(conn=Depends(get_conn)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM trades WHERE status = 'Pending'")
        rows = cur.fetchall()
        symbols = list(set([row['symbol'] for row in rows]))
        tickers_info = get_tickers_info(symbols)
        return [enrich_trade(row, tickers_info) for row in rows]

from pydantic import BaseModel
class TradeCreateRequest(BaseModel):
    rec_id: int
    user_id: int = 123
    symbol: str
    action: str
    price: float
    status: str = "pending_allocation"
    executed_at: Optional[str] = None

@router.post("/", response_model=dict)
def create_trade(trade: TradeCreateRequest, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO trades (rec_id, user_id, symbol, action, price, status, executed_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (trade.rec_id, trade.user_id, trade.symbol, trade.action, trade.price, trade.status, trade.executed_at)
        )
        trade_id = cur.fetchone()[0]
        conn.commit()
    return {"success": True, "trade_id": trade_id}

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

class Allocation(BaseModel):
    trade_id: int
    quantity: int
class AllocationRequest(BaseModel):
    allocations: List[Allocation]
    user_id: int

@router.post("/allocate")
def allocate_trades(request: AllocationRequest, conn=Depends(get_conn)):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get user balance
            cur.execute("SELECT balance FROM users WHERE id = %s", (request.user_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            balance = float(row["balance"])
            # Calculate total cost
            total_cost = 0.0
            for alloc in request.allocations:
                cur.execute("SELECT price FROM trades WHERE id = %s", (alloc.trade_id,))
                trade = cur.fetchone()
                if not trade:
                    raise HTTPException(status_code=404, detail=f"Trade {alloc.trade_id} not found")
                total_cost += float(trade["price"]) * alloc.quantity
            if total_cost > balance:
                raise HTTPException(status_code=400, detail="Insufficient balance")
            # Update trades and user balance
            for alloc in request.allocations:
                cur.execute("UPDATE trades SET quantity = %s, status = 'active' WHERE id = %s", (alloc.quantity, alloc.trade_id))
            cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (total_cost, request.user_id))
            conn.commit()
    return {"success": True, "total_cost": total_cost}
