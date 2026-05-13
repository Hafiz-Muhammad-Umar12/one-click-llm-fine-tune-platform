from celery import Celery
from src.core.config import settings

celery_app = Celery("tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.task_routes = {
    "src.datasets.jobs.tasks.*": {"queue": "dataset-tasks"},
}

celery_app.autodiscover_tasks(["src.datasets.jobs"])
