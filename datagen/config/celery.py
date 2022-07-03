from django.conf import settings

from celery import Celery, Task


app = Celery("config", broker=settings.CELERY_BROKER)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object(settings, namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self: Task) -> None:
    print(f"Request: {self.request!r}")
