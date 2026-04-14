from celery import Celery
from celery.schedules import crontab

from metax_application import METAX_APPLICATION

celery_app = Celery(
    main="metax",
    backend=METAX_APPLICATION.get_configs().celery_result_backend_url,
    broker=METAX_APPLICATION.get_configs().celery_broker_url,
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
