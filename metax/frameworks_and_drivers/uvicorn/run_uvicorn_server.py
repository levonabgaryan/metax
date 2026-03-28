import logging

import uvicorn

from config_ import metax_configs

logger = logging.getLogger(__name__)

_DJANGO_ASGI_APP = "django_framework.asgi:application"


def run_django_uvicorn_server() -> None:
    host = metax_configs.django_host
    port = metax_configs.django_port
    project_root_ = metax_configs.project_root_pythonpath

    logger.info("STARTUP | Task: Web Server (uvicorn) | Status: RUNNING | Address: http://%s:%s", host, port)

    uvicorn.run(_DJANGO_ASGI_APP, host=host, port=port, reload=True, reload_dirs=[project_root_], loop="uvloop")
