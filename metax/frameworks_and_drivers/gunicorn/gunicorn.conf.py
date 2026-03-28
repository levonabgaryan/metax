# https://gunicorn.org/asgi/?h=gunicorn.conf.py#recommended-settings
# https://gunicorn.org/reference/settings/?h=gunicorn.conf.py#config
from config_ import metax_configs

bind = f"{metax_configs.django_host}:{metax_configs.django_port}"  # https://gunicorn.org/reference/settings/?query=gunicorn+--c#bind
reload = metax_configs.gunicorn_reload  # https://gunicorn.org/reference/settings/#reload
workers = metax_configs.gunicorn_workers_count  # https://gunicorn.org/reference/settings/#workers
max_requests = 1000  # https://gunicorn.org/reference/settings/#max_requests
worker_class = "uvicorn.workers.UvicornWorker"  # https://gunicorn.org/reference/settings/#worker_class
