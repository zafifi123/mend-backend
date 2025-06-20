from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import trades, news
from api.routes import watchlist, recommendations, insights, trending, suggestions, chat
from api.routes import user
from api.routes import market

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Only allow Vite/dev frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(insights.router, prefix="/api/insights", tags=["insights"])
app.include_router(trending.router, prefix="/api", tags=["trending", "movers"])
app.include_router(suggestions.router, prefix="/api/trades", tags=["suggestions"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(market.router, prefix="/api/financials", tags=["financials"])
