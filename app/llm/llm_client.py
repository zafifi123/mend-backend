import subprocess

def query_llm(prompt: str) -> str:
    result = subprocess.run(["ollama", "run", "mistral", prompt], capture_output=True, text=True)
    return result.stdout.strip()

def generate_trade_explanation(symbol: str, score: float, news: list) -> str:
    articles = "\n".join([f"- {a['title']}" for a in news[:3]])
    prompt = f"""
A trading bot has evaluated {symbol} with a risk score of {score:.2f}.
Recent news:
{articles}

Explain whether this is a good trade and why.
"""
    return query_llm(prompt)
