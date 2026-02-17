import json

def load_portfolio(path="data/portfolio.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
