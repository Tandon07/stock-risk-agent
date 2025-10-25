from newsapi import NewsApiClient
from transformers import pipeline
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv("NEWS_API_KEY"))
newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")

def get_sentiment(company_name: str):
    articles = newsapi.get_everything(q=company_name, language="en", page_size=5)
    if not articles["articles"]:
        return {"sentiment": 0, "articles": []}

    sentiments = []
    summarized = []
    for art in articles["articles"]:
        text = (art["title"] or "") + ". " + (art["description"] or "")
        s = finbert(text[:512])[0]  # label: POSITIVE/NEGATIVE/NEUTRAL
        label = s["label"].upper()
        val = {"POSITIVE": 1, "NEGATIVE": -1, "NEUTRAL": 0}[label]
        sentiments.append(val)
        summarized.append({
            "source": art["source"]["name"],
            "title": art["title"],
            "sentiment": s["label"]
        })
    avg_sentiment = sum(sentiments) / len(sentiments)
    return {"sentiment": avg_sentiment, "articles": summarized}
# print(get_sentiment(company_name="Infosys"))