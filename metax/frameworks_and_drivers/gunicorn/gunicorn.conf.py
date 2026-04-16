# https://gunicorn.org/asgi/?h=gunicorn.conf.py#recommended-settings
# https://gunicorn.org/reference/settings/?h=gunicorn.conf.py#config
from metax_bootstrap import METAX_CONFIGS

_configs = METAX_CONFIGS

bind = f"{_configs.django_host}:{_configs.django_port}"  # https://gunicorn.org/reference/settings/?query=gunicorn+--c#bind
reload = _configs.gunicorn_reload  # https://gunicorn.org/reference/settings/#reload
workers = _configs.gunicorn_workers_count  # https://gunicorn.org/reference/settings/#workers
max_requests = 1000  # https://gunicorn.org/reference/settings/#max_requests
worker_class = "uvicorn.workers.UvicornWorker"  # https://gunicorn.org/reference/settings/#worker_class
asgi_loop = "uvloop"  # https://gunicorn.org/reference/settings/?query=gunicorn+--c#asgi_loop
