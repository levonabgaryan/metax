import asyncio
from typing import Any

from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging, worker_process_init, worker_process_shutdown

from metax_bootstrap import get_metax_lifespan_manager
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


@worker_process_init.connect
def init_celery_app(**kwargs: Any) -> None:  # noqa: ARG001
    asyncio.run(_init_celery_app())


async def _init_celery_app() -> None:
    metax_application_manager = get_metax_lifespan_manager()
    # Run startup pipeline in strict order.
    await metax_application_manager.init_di_container_resources()
    metax_application_manager.configure_django_app()
    # Django setup may override logging config, so apply ours after it.
    metax_application_manager.configure_logger()
    await metax_application_manager.run_entrypoints()
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Celery app initialized")


@worker_process_shutdown.connect
def shutdown_handler(**kwargs: Any) -> None:  # noqa: ARG001
    asyncio.run(_shutdown_handler())


async def _shutdown_handler() -> None:
    metax_application_manager = get_metax_lifespan_manager()
    await metax_application_manager.shutdown_di_container_resources()


@setup_logging.connect
def config_loggers(setup_event: None = None, **kwargs: Any) -> bool:  # noqa: ARG001
    metax_application_manager = get_metax_lifespan_manager()
    metax_application_manager.configure_logger()
    return True


# Ensure task decorators are evaluated and tasks are registered.
from . import tasks  # noqa: F401,E402
