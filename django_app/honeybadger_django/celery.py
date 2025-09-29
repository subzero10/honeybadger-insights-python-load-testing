import os
from celery import Celery
from dotenv import load_dotenv
from honeybadger.contrib import CeleryHoneybadger

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'honeybadger_django.settings')

app = Celery('honeybadger_django')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.update(
    HONEYBADGER_ENVIRONMENT = os.getenv('HONEYBADGER_ENVIRONMENT', 'production'),
    HONEYBADGER_API_KEY = os.getenv('HONEYBADGER_API_KEY'),
    HONEYBADGER_INSIGHTS_ENABLED = os.getenv('HONEYBADGER_INSIGHTS_ENABLED', False)
)
app.autodiscover_tasks()
CeleryHoneybadger(app, report_exceptions=True)
