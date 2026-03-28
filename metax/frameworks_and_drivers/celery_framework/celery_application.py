import logging
from typing import Any

from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger

from config_ import metax_configs
from logger.logger import init_logger

celery_app = Celery(
    main="metax",
    backend=metax_configs.celery_result_backend_url,
    broker=metax_configs.celery_broker_url,
)

celery_app.conf.timezone = "Asia/Yerevan"
celery_app.conf.enable_utc = True

celery_app.conf.beat_schedule = {
    "run-daily-task-at-0100": {
        "task": "CollectDiscountedProducts",
        "schedule": crontab(hour=1, minute=0),
        "options": {"queue": "default"},
    },
}


@after_setup_logger.connect
def setup_celery_logger(logger: logging.Logger, *args: Any, **kwargs: Any) -> None:
    """
    This signal ensures that when Celery starts its worker,
    it initializes project's custom non-blocking logger.
    """
    init_logger()
