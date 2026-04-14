from celery import Celery
from celery.schedules import crontab

from metax_configs import METAX_CONFIGS

celery_app = Celery(
    main="metax",
    backend=METAX_CONFIGS.celery_result_backend_url,
    broker=METAX_CONFIGS.celery_broker_url,
)

celery_app.conf.update(
    timezone="Asia/Yerevan",
    enable_utc=True,
    beat_schedule={
        "run-daily-task-at-0100": {
            "task": "CollectDiscountedProducts",
            "schedule": crontab(hour=1, minute=0),
            "options": {"queue": "default"},
        },
    },
)
