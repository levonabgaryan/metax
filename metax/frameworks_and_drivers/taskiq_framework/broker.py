from typing import Any

from taskiq import TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from metax.frameworks_and_drivers.taskiq_framework.middlewares import DjangoAdminTaskiqMiddleware
from metax_bootstrap import METAX_CONFIGS, METAX_LIFESPAN_MANAGER

result_backend: RedisAsyncResultBackend[Any] = RedisAsyncResultBackend(
    redis_url=METAX_CONFIGS.redis_url,
    result_ex_time=86400,
)

broker_ = RedisStreamBroker(
    url=METAX_CONFIGS.redis_url,
).with_result_backend(result_backend)

scheduler = TaskiqScheduler(  # Taskiq scheduler assumes that if time has no specific timezone, it's in UTC.
    broker=broker_,
    sources=[LabelScheduleSource(broker_)],
)


@broker_.on_event(TaskiqEvents.WORKER_STARTUP)
async def worker_startup(state: TaskiqState) -> None:  # noqa: ARG001
    # https://github.com/taskiq-python/taskiq/blob/3f1d0d1dd2b4918189c7f643108abffaed42599c/docs/guide/state-and-deps.md?plain=1#L65
    metax_lifespan_manager = METAX_LIFESPAN_MANAGER
    metax_lifespan_manager.configure_logger()
    await metax_lifespan_manager.init_metax_container_resources()
    metax_lifespan_manager.configure_django_app()


@broker_.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def worker_shutdown(state: TaskiqState) -> None:  # noqa: ARG001
    metax_lifespan_manager = METAX_LIFESPAN_MANAGER
    await metax_lifespan_manager.shutdown_metax_container_resources()


broker_.add_middlewares(DjangoAdminTaskiqMiddleware())
