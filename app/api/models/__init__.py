from pydantic import BaseModel
from typing import Optional, List

class WatchlistItem(BaseModel):
    symbol: str
    name: str
    price: float
    change: str
    volume: int
    marketCap: str
    sector: str

class Recommendation(BaseModel):
    id: int
    symbol: str
    name: str
    recommendation: str
    confidence: int
    price: str
    change: str
    reasoning: str
    risk: str
    timeframe: str
    sector: str

class MarketInsight(BaseModel):
    sentiment: str
    topSectors: List[str]
    volatilityAlert: str

class TrendingStock(BaseModel):
    symbol: str
    name: str

class TopMover(BaseModel):
    symbol: str
    name: str
    change: str

class NewsArticle(BaseModel):
    title: str
    url: str

class TradeSuggestion(BaseModel):
    symbol: str
    recommendation: str
    score: float

class ChatMessage(BaseModel):
    message: str

class TradeEnriched(BaseModel):
    id: int
    symbol: str
    action: str
    reason: str
    price: float
    quantity: Optional[int]
    status: str
    executed_at: Optional[str]
    name: str
    change: str
    volume: int
    marketCap: str
    sector: str
