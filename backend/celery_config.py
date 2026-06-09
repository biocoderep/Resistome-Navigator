"""Celery configuration for async task processing."""

import os
from datetime import timedelta

# Broker settings
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Task settings
task_serializer = "json"
accept_content = ["json"]
result_serializer = "json"
timezone = "UTC"
enable_utc = True

# Task execution settings
task_track_started = True
task_time_limit = 30 * 60  # 30 minutes hard limit
task_soft_time_limit = 28 * 60  # 28 minutes soft limit
worker_max_tasks_per_child = 1000

# Retry settings
task_autoretry_for = (Exception,)
task_max_retries = 3
task_default_retry_delay = 60  # 1 minute

# Worker settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000

# Result backend settings
result_expires = 3600  # 1 hour
result_persistent = True

# Periodic task settings
beat_scheduler = "celery.beat:PersistentScheduler"
beat_schedule = {
    "cleanup-old-results": {
        "task": "backend.tasks.cleanup_old_results",
        "schedule": timedelta(hours=6),
    },
    "health-check": {
        "task": "backend.tasks.health_check",
        "schedule": timedelta(minutes=5),
    },
}

# Import settings from environment
if os.getenv("CELERY_ALWAYS_EAGER"):
    task_always_eager = True
    task_eager_propagates = True
