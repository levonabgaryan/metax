# https://gunicorn.org/asgi/?h=gunicorn.conf.py#recommended-settings
# https://gunicorn.org/reference/settings/?h=gunicorn.conf.py#config
from __future__ import annotations
from config_ import metax_configs

bind = f"{metax_configs.django_host}:{metax_configs.django_port}"

reload = (
    metax_configs.debug
)  # https://gunicorn.org/reference/settings/#reloadhttps://gunicorn.org/reference/settings/#reload
workers = metax_configs.gunicorn_workers_count  # https://gunicorn.org/reference/settings/#workers
max_requests = 1000  # https://gunicorn.org/reference/settings/#max_requests
worker_class = "uvicorn.workers.UvicornWorker"  # https://gunicorn.org/reference/settings/#worker_class
