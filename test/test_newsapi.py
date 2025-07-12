import os
import sys
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def check_env():
    print("Checking environment configuration for NewsAPI key...")
    api_key = Config.NEWS_API_KEY
    if not api_key:
        print("FAILED: NEWS_API_KEY is not configured in the environment.")
        return False
    print("SUCCESS: NEWS_API_KEY is present in the environment.")
    return True

def fetch_news():
    print("Fetching news articles from NewsAPI...")
    api_key = Config.NEWS_API_KEY
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "us",
        "pageSize": 4,
        "apiKey": api_key
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            if not articles:
                print("FAILED: No articles returned.")
                return False
            print(f"SUCCESS: Fetched {len(articles)} articles.")
            for i, article in enumerate(articles, 1):
                title = article.get("title", "No Title")
                source = article.get("source", {}).get("name", "Unknown Source")
                print(f"{i}. {title} (Source: {source})")
            return True
        else:
            print("FAILED: NewsAPI request failed.")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Exception occurred while fetching news: {e}")
        return False

def main():
    env_ok = check_env()
    news_ok = fetch_news() if env_ok else False
    print("\nSummary:")
    print(f"Environment configured: {env_ok}")
    print(f"Can fetch news: {news_ok}")
    if env_ok and news_ok:
        print("Test result: NewsAPI integration is working.")
    else:
        print("Test result: NewsAPI integration is NOT working.")

if __name__ == "__main__":
    main() 