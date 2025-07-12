from celery.schedules import crontab
from celery_app import celery
from tasks import fetch_news_task, daily_delivery_task, cleanup_audio_task, health_check_task

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Daily news delivery at 7:30 AM
    sender.add_periodic_task(
        crontab(hour=7, minute=30),
        daily_delivery_task.s(),
        name='daily-news-delivery'
    )
    
    # Fetch news every 6 hours
    sender.add_periodic_task(
        crontab(hour='*/6'),
        fetch_news_task.s(),
        name='fetch-latest-news'
    )
    
    # Cleanup old audio files daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_audio_task.s(),
        name='cleanup-old-audio'
    )
    
    # Health check every hour
    sender.add_periodic_task(
        crontab(hour='*/1'),
        health_check_task.s(),
        name='system-health-check'
    ) 