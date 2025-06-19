from fastapi import APIRouter, Depends, Query, Body
from api.core.db import get_conn
from pydantic import BaseModel

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