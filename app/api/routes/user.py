from fastapi import APIRouter, Depends, Query, Body
from api.core.db import get_conn
from pydantic import BaseModel
from api.models import UserStats
from psycopg2.extras import RealDictCursor
from api.core.cache import get_tickers_info

router = APIRouter()

@router.get("/balance")
def get_user_balance(user_id: int = Query(...), conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user_id": user_id, "balance": float(row[0])}

class BalanceUpdateRequest(BaseModel):
    user_id: int
    new_balance: float

@router.put("/balance")
def update_user_balance(request: BalanceUpdateRequest, conn=Depends(get_conn)):
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET balance = %s WHERE id = %s", (request.new_balance, request.user_id))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
    return {"success": True, "user_id": request.user_id, "new_balance": request.new_balance}

@router.get("/stats", response_model=UserStats)
def get_user_stats(user_id: int = Query(...), conn=Depends(get_conn)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM trades WHERE user_id = %s", (user_id,))
        trades = cur.fetchall()
        if not trades:
            return UserStats(
                portfolio_value=0.0, portfolio_change=0.0, portfolio_change_percent=0.0,
                active_positions=0, unique_symbols=0, win_rate=0.0,
                risk_score=0.0, risk_level="None"
            )

        symbols = list(set(t["symbol"] for t in trades))
        if not symbols:
             return UserStats(
                portfolio_value=0.0, portfolio_change=0.0, portfolio_change_percent=0.0,
                active_positions=0, unique_symbols=0, win_rate=0.0,
                risk_score=0.0, risk_level="None"
            )
            
        tickers_info = get_tickers_info(symbols)

        active_positions = sum(1 for t in trades if t["status"].lower() == "active")
        unique_symbols = len(symbols)
        
        portfolio_value = 0.0
        portfolio_cost = 0.0
        for t in trades:
            if t["status"].lower() == "active" and t["quantity"]:
                try:
                    info = tickers_info.get(t["symbol"], {})
                    price = float(info.get("regularMarketPrice", float(t["price"])))
                    quantity = float(t["quantity"])
                    portfolio_value += price * quantity
                    portfolio_cost += float(t["price"]) * quantity
                except Exception:
                    portfolio_value += float(t["price"]) * float(t["quantity"])
                    portfolio_cost += float(t["price"]) * float(t["quantity"])

        portfolio_change = portfolio_value - portfolio_cost
        portfolio_change_percent = (portfolio_change / portfolio_cost) if portfolio_cost else 0.0
        
        closed_trades = [t for t in trades if t["status"].lower() == "closed" and t["quantity"]]
        wins = 0
        for t in closed_trades:
            try:
                info = tickers_info.get(t["symbol"], {})
                price = float(info.get("regularMarketPrice", float(t["price"])))
                if (t["action"].lower() == "buy" and price > float(t["price"])) or \
                   (t["action"].lower() == "sell" and price < float(t["price"])):
                    wins += 1
            except Exception:
                continue
                
        win_rate = (wins / len(closed_trades)) if closed_trades else 0.0
        
        risk_score = min(5.0, active_positions * 1.0)
        risk_level = "Low" if risk_score < 2 else "Moderate" if risk_score < 4 else "High"

        return UserStats(
            portfolio_value=portfolio_value, portfolio_change=portfolio_change,
            portfolio_change_percent=portfolio_change_percent, active_positions=active_positions,
            unique_symbols=unique_symbols, win_rate=win_rate,
            risk_score=risk_score, risk_level=risk_level
        ) 