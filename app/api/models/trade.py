from pydantic import BaseModel

class Trade(BaseModel):
    id: int
    symbol: str
    action: str
