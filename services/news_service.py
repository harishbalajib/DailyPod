import requests
import json
from datetime import datetime, timedelta
from config import Config
from models import db, NewsArticle, SystemLog

class NewsService:
    def __init__(self):
        self.api_key = Config.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2"
        
    def fetch_news(self, category='general', language='en', count=10):
        try:
            yesterday = datetime.now() - timedelta(days=1)
            from_date = yesterday.strftime('%Y-%m-%d')
            
            url = f"{self.base_url}/top-headlines"
            params = {
                'country': 'us',
                'category': category,
                'language': language,
                'pageSize': count,
                'from': from_date,
                'apiKey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'ok':
                articles = []
                for article_data in data['articles']:
                    existing = NewsArticle.query.filter_by(
                        title=article_data['title'],
                        source=article_data['source']['name']
                    ).first()
                    
                    if not existing:
                        article = NewsArticle(
                            title=article_data['title'],
                            content=article_data.get('description', '') or article_data.get('content', ''),
                            source=article_data['source']['name'],
                            url=article_data['url'],
                            category=category,
                            language=language
                        )
                        db.session.add(article)
                        articles.append(article)
                
                db.session.commit()
                
                self._log_system('info', f"Fetched {len(articles)} new articles for category: {category}, language: {language}")
                
                return articles
            else:
                self._log_system('error', f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            self._log_system('error', f"NewsAPI request failed: {str(e)}")
            return []
        except Exception as e:
            self._log_system('error', f"Error fetching news: {str(e)}")
            return []
    
    def fetch_all_categories(self, language='en'):
        all_articles = []
        
        for category in Config.NEWS_CATEGORIES:
            articles = self.fetch_news(category=category, language=language, count=5)
            all_articles.extend(articles)
        
        return all_articles
    
    def fetch_multilingual_news(self):
        all_articles = []
        
        for language in Config.SUPPORTED_LANGUAGES:
            articles = self.fetch_all_categories(language=language)
            all_articles.extend(articles)
        
        return all_articles
    
    def get_recent_articles(self, language='en', category=None, limit=10):
        query = NewsArticle.query.filter_by(language=language)
        
        if category:
            query = query.filter_by(category=category)
        
        return query.order_by(NewsArticle.created_at.desc()).limit(limit).all()
    
    def _log_system(self, level, message):
        log = SystemLog(level=level, message=message)
        db.session.add(log)
        db.session.commit() 