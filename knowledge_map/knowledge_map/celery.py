import os
from celery import Celery

# Point to your base settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'knowledge_map.settings.base')

app = Celery('knowledge_map')

# Load celery config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()