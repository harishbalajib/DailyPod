from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from config import Config
from models import db, User, NewsArticle, DeliveryLog, SystemLog
from services.news_service import NewsService
from services.ai_service import AIService
from services.tts_service import TTSService
from services.whatsapp_service import WhatsAppService

class NewsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.news_service = NewsService()
        self.ai_service = AIService()
        self.tts_service = TTSService()
        self.whatsapp_service = WhatsAppService()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def start(self):
        try:
            self.scheduler.add_job(
                func=self.daily_news_delivery,
                trigger=CronTrigger(hour=7, minute=30),
                id='daily_news_delivery',
                name='Daily News Delivery at 7:30 AM',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                func=self.fetch_latest_news,
                trigger=CronTrigger(hour='*/6'),
                id='fetch_latest_news',
                name='Fetch Latest News Every 6 Hours',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                func=self.cleanup_old_audio,
                trigger=CronTrigger(hour=2, minute=0),
                id='cleanup_audio',
                name='Cleanup Old Audio Files',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                func=self.system_health_check,
                trigger=CronTrigger(hour='*/1'),
                id='health_check',
                name='System Health Check',
                replace_existing=True
            )
            
            self.scheduler.start()
            self._log_system('info', 'News scheduler started successfully')
            
        except Exception as e:
            self._log_system('error', f'Failed to start scheduler: {str(e)}')
            raise
    
    def stop(self):
        self.scheduler.shutdown()
        self._log_system('info', 'News scheduler stopped')
    
    def daily_news_delivery(self):
        try:
            self._log_system('info', 'Starting daily news delivery process')
            
            active_users = User.query.filter_by(is_active=True).all()
            
            if not active_users:
                self._log_system('info', 'No active users found for daily delivery')
                return
            
            users_by_language = {}
            for user in active_users:
                lang = user.language
                if lang not in users_by_language:
                    users_by_language[lang] = []
                users_by_language[lang].append(user)
            
            for language, users in users_by_language.items():
                self._process_language_group(language, users)
            
            self._log_system('info', f'Daily news delivery completed for {len(active_users)} users')
            
        except Exception as e:
            self._log_system('error', f'Error in daily news delivery: {str(e)}')
    
    def _process_language_group(self, language, users):
        try:
            articles = self.news_service.get_recent_articles(language=language, limit=10)
            
            if not articles:
                articles = self.news_service.fetch_news(language=language, count=10)
            
            if not articles:
                self._log_system('warning', f'No articles available for language: {language}')
                return
            
            summary = self.ai_service.create_daily_summary(articles, language)
            
            if not summary:
                self._log_system('error', f'Failed to create summary for language: {language}')
                return
            
            audio_filename = self.tts_service.create_daily_audio(summary, language)
            
            if not audio_filename:
                self._log_system('error', f'Failed to create audio for language: {language}')
                return
            
            success_count = 0
            for user in users:
                try:
                    if self.whatsapp_service.send_daily_news(user, audio_filename, summary):
                        success_count += 1
                    else:
                        self.whatsapp_service.send_error_message(user.phone_number, language)
                except Exception as e:
                    self._log_system('error', f'Failed to send news to {user.phone_number}: {str(e)}')
            
            self._log_system('info', f'Successfully delivered news to {success_count}/{len(users)} users in {language}')
            
        except Exception as e:
            self._log_system('error', f'Error processing language group {language}: {str(e)}')
    
    def fetch_latest_news(self):
        try:
            self._log_system('info', 'Fetching latest news from all sources')
            
            articles = self.news_service.fetch_multilingual_news()
            
            for article in articles:
                if not article.summary:
                    summary = self.ai_service.summarize_article(
                        article.title, 
                        article.content, 
                        article.language
                    )
                    if summary:
                        article.summary = summary
            
            db.session.commit()
            
            self._log_system('info', f'Fetched and processed {len(articles)} new articles')
            
        except Exception as e:
            self._log_system('error', f'Error fetching latest news: {str(e)}')
    
    def cleanup_old_audio(self):
        try:
            self.tts_service.cleanup_old_audio(days=7)
        except Exception as e:
            self._log_system('error', f'Error cleaning up audio files: {str(e)}')
    
    def system_health_check(self):
        try:
            active_users = User.query.filter_by(is_active=True).count()
            
            recent_articles = NewsArticle.query.filter(
                NewsArticle.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            failed_deliveries = DeliveryLog.query.filter(
                DeliveryLog.status == 'failed',
                DeliveryLog.sent_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
            
            self._log_system('info', f'Health check - Active users: {active_users}, Recent articles: {recent_articles}, Failed deliveries: {failed_deliveries}')
            
        except Exception as e:
            self._log_system('error', f'Error in health check: {str(e)}')
    
    def manual_delivery(self, language='en'):
        try:
            self._log_system('info', f'Manual delivery triggered for language: {language}')
            
            users = User.query.filter_by(is_active=True, language=language).all()
            if users:
                self._process_language_group(language, users)
            else:
                self._log_system('warning', f'No active users found for language: {language}')
                
        except Exception as e:
            self._log_system('error', f'Error in manual delivery: {str(e)}')
    
    def _log_system(self, level, message):
        log = SystemLog(level=level, message=message)
        db.session.add(log)
        db.session.commit()
        
        if level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)
        else:
            self.logger.info(message) 