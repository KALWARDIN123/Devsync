"""
Celery configuration for DevSync project.
"""
import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('devsync')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery
app.conf.update(
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_time_limit=900,  # 15 minutes
    task_soft_time_limit=600,  # 10 minutes
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=4,
    
    # Result backend settings
    result_expires=timedelta(days=1),
    
    # Error handling
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# Task routing
app.conf.task_routes = {
    'ai.services.code_review.async_code_review': {'queue': 'ai'},
    'chat.tasks.*': {'queue': 'chat'},
    'analytics.tasks.*': {'queue': 'analytics'},
}

# Scheduled tasks
app.conf.beat_schedule = {
    'cleanup-old-messages': {
        'task': 'chat.tasks.cleanup_old_messages',
        'schedule': crontab(hour=0, minute=0),  # Run daily at midnight
        'args': (),
    },
    'generate-daily-analytics': {
        'task': 'analytics.tasks.generate_daily_report',
        'schedule': crontab(hour=1, minute=0),  # Run daily at 1 AM
        'args': (),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task for debugging purposes."""
    print(f'Request: {self.request!r}') 