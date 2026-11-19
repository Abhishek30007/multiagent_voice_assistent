from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "personal_ai_twin_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minutes hard limit
    beat_schedule={
        "periodic-incremental-sync": {
            "task": "app.workers.tasks.task_scheduled_sync_all",
            "schedule": crontab(minute=f"*/{settings.AUTO_SYNC_INTERVAL_MINUTES}"),
        },
    },
)
