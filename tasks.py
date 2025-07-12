from celery import shared_task
from celery_app import celery
from datetime import datetime
from config import Config
from models import db, User, NewsArticle, DeliveryLog, SystemLog
from services.news_service import NewsService
from services.ai_service import AIService
from services.tts_service import TTSService
from services.whatsapp_service import WhatsAppService

@shared_task
def fetch_news_task():
    try:
        news_service = NewsService()
        articles = news_service.fetch_multilingual_news()
        
        for article in articles:
            if not article.summary:
                ai_service = AIService()
                summary = ai_service.summarize_article(
                    article.title, 
                    article.content, 
                    article.language
                )
                if summary:
                    article.summary = summary
        
        db.session.commit()
        return f"Fetched and processed {len(articles)} articles"
    except Exception as e:
        return f"Error fetching news: {str(e)}"

@shared_task
def daily_delivery_task():
    try:
        active_users = User.query.filter_by(is_active=True).all()
        
        if not active_users:
            return "No active users found"
        
        users_by_language = {}
        for user in active_users:
            lang = user.language
            if lang not in users_by_language:
                users_by_language[lang] = []
            users_by_language[lang].append(user)
        
        total_sent = 0
        for language, users in users_by_language.items():
            result = process_language_delivery.delay(language, [u.id for u in users])
            total_sent += len(users)
        
        return f"Initiated delivery for {total_sent} users"
    except Exception as e:
        return f"Error in daily delivery: {str(e)}"

@shared_task
def process_language_delivery(language, user_ids):
    try:
        news_service = NewsService()
        ai_service = AIService()
        tts_service = TTSService()
        whatsapp_service = WhatsAppService()
        
        articles = news_service.get_recent_articles(language=language, limit=10)
        
        if not articles:
            articles = news_service.fetch_news(language=language, count=10)
        
        if not articles:
            return f"No articles available for language: {language}"
        
        summary = ai_service.create_daily_summary(articles, language)
        
        if not summary:
            return f"Failed to create summary for language: {language}"
        
        audio_filename = tts_service.create_daily_audio(summary, language)
        
        if not audio_filename:
            return f"Failed to create audio for language: {language}"
        
        success_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user and user.is_active:
                try:
                    if whatsapp_service.send_daily_news(user, audio_filename, summary):
                        success_count += 1
                    else:
                        whatsapp_service.send_error_message(user.phone_number, language)
                except Exception as e:
                    pass
        
        return f"Successfully delivered to {success_count}/{len(user_ids)} users in {language}"
    except Exception as e:
        return f"Error processing language {language}: {str(e)}"

@shared_task
def cleanup_audio_task():
    try:
        tts_service = TTSService()
        tts_service.cleanup_old_audio(days=7)
        return "Audio cleanup completed"
    except Exception as e:
        return f"Error in audio cleanup: {str(e)}"

@shared_task
def health_check_task():
    try:
        active_users = User.query.filter_by(is_active=True).count()
        recent_articles = NewsArticle.query.filter(
            NewsArticle.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        failed_deliveries = DeliveryLog.query.filter(
            DeliveryLog.status == 'failed',
            DeliveryLog.sent_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return f"Health check - Active users: {active_users}, Recent articles: {recent_articles}, Failed deliveries: {failed_deliveries}"
    except Exception as e:
        return f"Error in health check: {str(e)}" 