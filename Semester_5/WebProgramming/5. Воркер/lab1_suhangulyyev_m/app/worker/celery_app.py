import logging  # noqa: E402
from logging.handlers import RotatingFileHandler  # noqa: E402
from celery import Celery  # noqa: E402
from celery.schedules import crontab  # noqa: E402

from app.core.config import settings  # noqa: E402


# Настройка логирования в файл
log_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log_file = "celery_worker.log"
file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(log_formatter)
celery_logger = logging.getLogger("celery_worker")
celery_logger.addHandler(file_handler)
celery_logger.setLevel(logging.INFO)

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
