from celery import Celery
from app.config import settings

celery_app = Celery(
    "outreach",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.campaign_tasks",
        "app.tasks.sheet_tasks",
        "app.tasks.inbox_tasks",
        "app.tasks.warmup_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    beat_schedule={
        "fetch-sheet-leads": {
            "task": "app.tasks.sheet_tasks.fetch_all_sheet_leads",
            "schedule": 300.0,
        },
        "check-gmail-inboxes": {
            "task": "app.tasks.inbox_tasks.check_all_inboxes",
            "schedule": 120.0,
        },
        "refresh-gmail-tokens": {
            "task": "app.tasks.inbox_tasks.refresh_all_tokens",
            "schedule": 3600.0,
        },
        "update-gmail-health": {
            "task": "app.tasks.inbox_tasks.update_all_health_scores",
            "schedule": 1800.0,
        },
        "process-warmup": {
            "task": "app.tasks.warmup_tasks.process_warmup_all",
            "schedule": 3600.0,
        },
        "reset-daily-counts": {
            "task": "app.tasks.campaign_tasks.reset_daily_counts",
            "schedule": 86400.0,
        },
    },
)
