import requests
from bs4 import BeautifulSoup

def fetch_news_articles(symbol: str):
    url = f"https://finance.yahoo.com/quote/{symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    for item in soup.select('a[aria-label]'):
        if item and item.text and item.get("href"):
            title = item.text.strip()
            link = item["href"]
            if link.startswith("/"):
                link = "https://finance.yahoo.com" + link
            articles.append({"title": title, "url": link})
        if len(articles) >= 10:
            break
    return articles

def fetch_general_news():
    url = "https://finance.yahoo.com/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    for item in soup.select('a[aria-label]'):
        if item and item.text and item.get("href"):
            title = item.text.strip()
            link = item["href"]
            if link.startswith("/"):
                link = "https://finance.yahoo.com" + link
            if not any(existing['title'] == title for existing in articles):
                 articles.append({"title": title, "url": link})
        if len(articles) >= 10:
            break
    return articles
