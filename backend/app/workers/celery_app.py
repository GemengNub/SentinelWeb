"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "disaster_detector",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Beat schedule
    beat_schedule={
        "poll-earthquakes": {
            "task": "app.workers.tasks.poll_earthquakes",
            "schedule": settings.EARTHQUAKE_POLL_INTERVAL,
        },
        "poll-weather": {
            "task": "app.workers.tasks.poll_weather",
            "schedule": settings.WEATHER_POLL_INTERVAL,
        },
        "poll-noaa": {
            "task": "app.workers.tasks.poll_noaa",
            "schedule": settings.WEATHER_POLL_INTERVAL,
        },
        "poll-pagasa": {
            "task": "app.workers.tasks.poll_pagasa",
            "schedule": settings.EARTHQUAKE_POLL_INTERVAL,
        },
        "poll-jma": {
            "task": "app.workers.tasks.poll_jma",
            "schedule": settings.EARTHQUAKE_POLL_INTERVAL,
        },
        # "poll-firms": {
        #     "task": "app.workers.tasks.poll_firms",
        #     "schedule": 300.0,
        # },  # FIRMS API requires different authentication - disabled for now
        "process-pending-events": {
            "task": "app.workers.tasks.process_pending_events",
            "schedule": 30.0,  # Every 30 seconds
        },
        "generate-predictions": {
            "task": "app.workers.tasks.generate_predictions",
            "schedule": 300.0,  # Every 5 minutes
        },
        "cleanup-old-events": {
            "task": "app.workers.tasks.cleanup_old_events",
            "schedule": crontab(hour=0, minute=0),  # Daily at midnight
        },
        "send-daily-summary": {
            "task": "app.workers.tasks.send_daily_summary",
            "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
        },
    },
    
    # Routing
    task_routes={},
)


# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])
