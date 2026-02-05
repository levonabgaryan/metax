from celery import Celery
from celery.schedules import crontab

from config import discount_service_configs
from discount_service.frameworks_and_drivers.di import get_service_container

celery_app = Celery(
    main="discount_service",
    backend=discount_service_configs.celery_backend_url,
    broker=discount_service_configs.celery_broker_url,
)

celery_app.conf.timezone = "Asia/Yerevan"
celery_app.conf.enable_utc = True

service_container = get_service_container()
service_container.wire(
    modules=["discount_service.frameworks_and_drivers.celery_framework.tasks"],
)

celery_app.conf.beat_schedule = {
    "run-daily-task-at-0100": {
        "task": "tasks.collect_discounted_products_from_retailer",
        "schedule": crontab(hour=1, minute=0),
        "options": {"queue": "default"},
    },
}
