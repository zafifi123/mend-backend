from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, trades, news

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
