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
            url = f"{self.base_url}/top-headlines"
            params = {
                'country': 'us',
                'category': category,
                'language': language,
                'pageSize': count,
                'apiKey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'ok':
                articles = []
                for article_data in data['articles']:
                    try:
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
                    except Exception as e:
                        # If database operation fails, still return the article data
                        print(f"Database error for article {article_data['title']}: {e}")
                        # Create a simple article object without database
                        class SimpleArticle:
                            def __init__(self, title, content, source, url, category, language):
                                self.title = title
                                self.content = content
                                self.source = source
                                self.url = url
                                self.category = category
                                self.language = language
                                self.summary = None
                        
                        article = SimpleArticle(
                            title=article_data['title'],
                            content=article_data.get('description', '') or article_data.get('content', ''),
                            source=article_data['source']['name'],
                            url=article_data['url'],
                            category=category,
                            language=language
                        )
                        articles.append(article)
                
                try:
                    db.session.commit()
                except Exception as e:
                    print(f"Database commit error: {e}")
                
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
        try:
            query = NewsArticle.query.filter_by(language=language)
            
            if category:
                query = query.filter_by(category=category)
            
            return query.order_by(NewsArticle.created_at.desc()).limit(limit).all()
        except Exception as e:
            print(f"Database error getting recent articles: {e}")
            return []
    
    def _log_system(self, level, message):
        try:
            log = SystemLog(level=level, message=message)
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            # If we can't log to database, just print the message
            print(f"[{level.upper()}] {message}") 