"""
Celery configuration for CRM project.
This initializes celery using Djnago settings and shedule periodic tasks
"""

import os
from celery import Celery


# Set default Django setting module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')

# Create celery app instance
app = Celery('crm')

# Load settings from Django config
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    timezone='UTC',
)

# Auto-discover task from all installed apps
app.autodiscover_tasks()







