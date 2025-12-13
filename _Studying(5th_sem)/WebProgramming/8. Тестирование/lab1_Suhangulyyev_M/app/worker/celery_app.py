import os
from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init
from prometheus_client import multiprocess

from app.core.config import settings
from app.core.logger import configure_logger

configure_logger()


@worker_process_init.connect
def worker_init(**_):
    """
    Готовит директорию для метрик для каждого дочернего процесса Celery.
    """
    prometheus_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if prometheus_dir and not os.path.exists(prometheus_dir):
        os.makedirs(prometheus_dir, exist_ok=True)
    multiprocess.mark_process_dead(os.getpid())


celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

# Настройка расписания
celery_app.conf.beat_schedule = {
    "send-weekly-digest-every-sunday": {
        "task": "app.worker.tasks.send_weekly_digest",
        "schedule": crontab(day_of_week="sunday", hour=10, minute=0),
    },
}
celery_app.conf.timezone = "Europe/Moscow"
