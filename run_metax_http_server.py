import asyncio
import logging
import os
import sys
from pathlib import Path

import uvicorn

from metax_bootstrap import get_metax_lifespan_manager
from metax_configs import METAX_CONFIGS, BaseConfigs, DevConfigs
from metax_lifespan import MetaxAppLifespanManager

logger = logging.getLogger(__name__)

_DJANGO_ASGI_APP = "django_framework.asgi:application"


async def _run_django_gunicorn_server(_metax_app: MetaxAppLifespanManager, _metax_configs: BaseConfigs) -> None:

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(_metax_configs.project_root_pythonpath),
            str(_metax_configs.django_dir),
        ]
    )
    env["DJANGO_SETTINGS_MODULE"] = "django_framework.settings"

    host = _metax_configs.django_host
    port = _metax_configs.django_port

    gunicorn_conf = (
        Path(_metax_configs.project_root_pythonpath) / "metax/frameworks_and_drivers/gunicorn/gunicorn.conf.py"
    )

    command = [
        "-m",
        "gunicorn",
        f"--config={gunicorn_conf}",
        _DJANGO_ASGI_APP,
    ]
    process = await asyncio.create_subprocess_exec(
        sys.executable, *command, cwd=_metax_configs.django_dir, env=env
    )

    logger.info("STARTUP | Task: Web Server (gunicorn) | Status: RUNNING | Address: http://%s:%s", host, port)

    try:
        await process.wait()
    except asyncio.CancelledError:
        logger.info("SHUTDOWN | Task: Web Server | Status: Terminating (SIGTERM)...")
        process.terminate()
        await process.wait()
        logger.info("SHUTDOWN | Task: Web Server | Status: Clean Shutdown")

    if process.returncode != 0 and process.returncode != -15:
        logger.error("RUNTIME | Task: Web Server | Status: CRASHED | ExitCode: %s", process.returncode)
        msg = f"Gunicorn failed with exit code {process.returncode}"
        raise RuntimeError(msg)


def _run_django_uvicorn_server(_metax_app: MetaxAppLifespanManager, _metax_configs: BaseConfigs) -> None:
    host = _metax_configs.django_host
    port = _metax_configs.django_port
    project_root_ = _metax_configs.project_root_pythonpath
    django_dir_ = _metax_configs.django_dir

    # Ensure the reloader subprocess can import django_framework package.
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    extra_pythonpath = os.pathsep.join([str(project_root_), str(django_dir_)])
    os.environ["PYTHONPATH"] = (
        f"{extra_pythonpath}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else extra_pythonpath
    )
    os.environ["DJANGO_SETTINGS_MODULE"] = "django_framework.settings"

    logger.info("STARTUP | Task: Web Server (uvicorn) | Status: RUNNING | Address: http://%s:%s", host, port)

    uvicorn.run(
        _DJANGO_ASGI_APP,
        host=host,
        port=port,
        reload=True,
        reload_dirs=[project_root_, django_dir_],
        app_dir=str(django_dir_),
        loop="uvloop",
    )


if __name__ == "__main__":
    if isinstance(METAX_CONFIGS, DevConfigs):
        _run_django_uvicorn_server(get_metax_lifespan_manager(), METAX_CONFIGS)
    else:
        asyncio.run(_run_django_gunicorn_server(get_metax_lifespan_manager(), METAX_CONFIGS))
