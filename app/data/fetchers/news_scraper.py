def fetch_news_articles(symbol: str):
    return [
        { "title": f"News about {symbol}", "url": "https://example.com/article" },
        { "title": f"More on {symbol}", "url": "https://example.com/more" },
    ]
