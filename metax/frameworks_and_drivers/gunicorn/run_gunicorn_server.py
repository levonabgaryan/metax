import asyncio
import logging
import os
import sys
from pathlib import Path

from config_ import metax_configs

logger = logging.getLogger(__name__)


async def run_django_gunicorn_server() -> None:
    project_root_ = metax_configs.project_root_pythonpath
    django_path_ = metax_configs.django_dir
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([str(project_root_), str(django_path_)])
    env["DJANGO_SETTINGS_MODULE"] = "django_framework.settings"

    host = metax_configs.django_host
    port = metax_configs.django_port

    gunicorn_conf = (
        Path(metax_configs.project_root_pythonpath) / "metax/frameworks_and_drivers/gunicorn/gunicorn.conf.py"
    )

    command = [
        "-m",
        "gunicorn",
        f"--config={gunicorn_conf}",
        "django_framework.asgi:application",
    ]

    process = await asyncio.create_subprocess_exec(sys.executable, *command, cwd=metax_configs.django_dir, env=env)

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
        raise RuntimeError(f"Gunicorn failed with exit code {process.returncode}")
