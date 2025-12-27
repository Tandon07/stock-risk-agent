import datetime
import tweepy
import praw
from typing import List, Dict

# --- CONFIGURATION (Add your credentials here) ---
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAHQO6gEAAAAAnzRTYZ0U70I0Z9mnkRPgEYXklJI%3D9BgHQLUpyjHKiKadc2gV0gKVosZF6Fj4n2L9sqXIs8HWQg9MbG"

REDDIT_CLIENT_ID = "YOUR_REDDIT_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_REDDIT_CLIENT_SECRET"
REDDIT_USER_AGENT = "StockNewsScanner/1.0" # Any unique name works

# --- INITIALIZATION ---
# Twitter API v2 Client
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

# Reddit Client
reddit_client = praw.Reddit(
    client_id="16KH0wSC54WRygM1DaYnxA",
    client_secret="Fhf0If_Hhe002ZhpscHqWPAceKuQ2w",
    user_agent="AI-NEWS-AGENT"
)

def fetch_reddit_posts(stock_name: str) -> List[Dict]:
    """Fetches posts from specific finance subreddits with body text."""
    try:
        # Search relevant subreddits only
        target_subs = "stocks+investing+IndianStreetBets+IndianStockMarket+StockMarket"
        # query "Infosys" works better than natural sentences
        search_results = reddit_client.subreddit(target_subs).search(
            f'"{stock_name}"', 
            sort="new", 
            time_filter="week", 
            limit=5
        )
        
        return [{
            "source": "Reddit",
            "title": post.title,
            "content": (post.selftext[:250] + "...") if len(post.selftext) > 800 else (post.selftext or "[Link/Image Post]"),
            "url": post.url,
            "community": f"r/{post.subreddit.display_name}"
        } for post in search_results]
    except Exception as e:
        print(f"Reddit Error: {e}")
        return []

def fetch_twitter_posts(stock_name: str) -> List[Dict]:
    """Fetches high-quality financial tweets from the last 7 days."""
    try:
        # Query for name OR cashtag with financial context keywords
        query = f'("{stock_name}" OR ${stock_name}) (stock OR price OR news) lang:en -is:retweet'
        
        response = twitter_client.search_recent_tweets(
            query=query,
            max_results=10,
            tweet_fields=['created_at', 'text']
        )
        
        if not response.data:
            return []
            
        return [{
            "source": "Twitter",
            "title": f"Tweet on {tweet.created_at.strftime('%Y-%m-%d')}",
            "content": tweet.text.replace('\n', ' '),
            "url": f"https://twitter.com/twitter/status/{tweet.id}",
            "community": "X / Twitter"
        } for tweet in response.data]
    except Exception as e:
        print(f"Twitter Error: {e}")
        return []

def get_social_news(stock_name: str):
    print(f"\n{'='*60}")
    print(f"SOCIAL MEDIA ANALYSIS FOR: {stock_name.upper()}")
    print(f"{'='*60}")

    # Fetch Data
    reddit_news = fetch_reddit_posts(stock_name)
    twitter_news = fetch_twitter_posts(stock_name)
    
    all_news = reddit_news + twitter_news

    return all_news

#     if not all_news:
#         print("No recent social news found.")
#         return



# if __name__ == "__main__":
#     ticker = input("Enter Stock Name (e.g. Infosys): ")
#     print(run_stock_report(ticker))