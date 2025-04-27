import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telemedicine_project.settings')

app = Celery('telemedicine_project')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()  # Auto-discover tasks in all Django apps

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
