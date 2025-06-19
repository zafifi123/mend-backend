import requests
from bs4 import BeautifulSoup

def fetch_news_articles(symbol: str):
    url = f"https://finance.yahoo.com/quote/{symbol}/news"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    for item in soup.select("li.js-stream-content"):
        a = item.find("a")
        if a and a.text and a.get("href"):
            title = a.text.strip()
            link = a["href"]
            if link.startswith("/"):
                link = "https://finance.yahoo.com" + link
            articles.append({"title": title, "url": link})
        if len(articles) >= 10:
            break
    return articles
