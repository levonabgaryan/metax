from celery import Celery

from config import discount_service_configs

print(discount_service_configs.celery_backend_url)
celery_app = Celery(
    main="discount_service",
    backend=discount_service_configs.celery_backend_url,
    broker=discount_service_configs.celery_broker_url,
)
