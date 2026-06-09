"""Celery application initialization."""

from celery import Celery

# Initialize Celery app
app = Celery("amr_platform")

# Load configuration from celery_config.py
app.config_from_object("backend.celery_config")

# Auto-discover tasks from all registered apps
app.autodiscover_tasks(["backend.tasks"])

# Optional: Export as celery_app for command-line tools
celery_app = app

__all__ = ["app", "celery_app"]
