from celery import Celery
from config import Config

celery = Celery('dailypod',
                broker=Config.REDIS_URL,
                backend=Config.REDIS_URL,
                include=['tasks', 'celery_beat_schedule'])

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
) 