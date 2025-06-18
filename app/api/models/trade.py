from pydantic import BaseModel

class Trade(BaseModel):
    symbol: str
    action: str
    reason: str
