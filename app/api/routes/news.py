from fastapi import APIRouter
from data.fetchers.news_scraper import fetch_news_articles

router = APIRouter()

@router.get("/{symbol}")
async def get_news(symbol: str):
    return fetch_news_articles(symbol)
