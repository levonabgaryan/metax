from __future__ import annotations

import asyncio
from dataclasses import dataclass

from entrypoint import run_entrypoint
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from metax_configs import METAX_CONFIGS, BaseConfigs
from metax_logger.logger import init_logger


@dataclass(slots=True)
class AppState:
    logger_configured: bool = False
    container_configured: bool = False
    django_configured: bool = False

    @property
    def is_ready(self) -> bool:
        return all([self.container_configured, self.logger_configured, self.django_configured])


class MetaxApplicationManager:
    """Bootstraps application dependencies for a single process.

    This class provides all necessary configs, dependencies, so for example
    instead of using METAX_CONFIGS, you should use METAX_APPLICATION.get_configs()

    Note:
        Ensure external services are already running (Postgres, OpenSearch, etc.).
        Recommended call order:
        1) init_di_container_resources
        2) configure_logger
        3) run_entrypoints
        4) shutdown_di_container_resources (call in a finally block)

        This manager is intended to be instantiated once per process.
        It is safe to run logger/bootstrap in worker, beat, and web processes separately
        because each process has its own memory and runtime state.
    """

    def __init__(
        self,
        metax_di_container: MetaxContainer,
        metax_configs: BaseConfigs,
    ) -> None:
        self.__metax_di_container = metax_di_container
        self.__metax_configs = metax_configs
        self.__lock = asyncio.Lock()

        self.__app_state = AppState()

    def get_di_container(self) -> MetaxContainer:
        if not self.__app_state.is_ready:
            msg = "Application is not ready."
            raise RuntimeError(msg)
        return self.__metax_di_container

    def get_configs(self) -> BaseConfigs:
        return self.__metax_configs

    async def init_di_container_resources(self) -> None:
        async with self.__lock:
            if not self.__app_state.container_configured:
                self.__metax_di_container.config.from_pydantic(self.__metax_configs)

                init_task = self.__metax_di_container.init_resources()
                if init_task:
                    await init_task
                    self.__app_state.container_configured = True

    async def shutdown_di_container_resources(self) -> None:
        shutdown_task = self.__metax_di_container.shutdown_resources()
        if shutdown_task:
            await shutdown_task
            self.__app_state.container_configured = False

    async def configure_logger(self) -> None:
        async with self.__lock:
            if not self.__app_state.logger_configured:
                init_logger(metax_configs=self.__metax_configs)
                self.__app_state.logger_configured = True

    async def run_entrypoints(self) -> None:
        if not self.__app_state.is_ready:
            msg = (
                "Application is not ready. Ensure logger, DI container resources, "
                "and Django are configured before running entrypoints."
            )
            raise RuntimeError(msg)
        opensearch_async_client = await self.__metax_di_container.opensearch_async_client.async_()
        await run_entrypoint(client=opensearch_async_client, metax_configs=self.get_configs())

    def configure_django_app(self) -> None:
        if self.__app_state.django_configured:
            return

        import django
        from django.conf import settings

        if not settings.configured:
            settings.configure()
        django.setup()
        self.__app_state.django_configured = True


METAX_APPLICATION_MANAGER = MetaxApplicationManager(
    metax_configs=METAX_CONFIGS, metax_di_container=MetaxContainer()
)

__all__ = ["METAX_APPLICATION_MANAGER", "MetaxApplicationManager"]
