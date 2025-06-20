from fastapi import APIRouter
from api.data.fetchers.news_scraper import fetch_news_articles, fetch_general_news

router = APIRouter()

@router.get("/general")
async def get_general_news():
    return fetch_general_news()

@router.get("/{symbol}")
async def get_news(symbol: str):
    return fetch_news_articles(symbol)
