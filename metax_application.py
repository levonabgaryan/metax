import asyncio
from enum import Enum, auto
from types import TracebackType
from typing import Self

from entrypoint import run_entrypoint
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from metax_configs import METAX_CONFIGS, BaseConfigs
from metax_logger.logger import init_logger


class MetaxAppState(Enum):
    READY = auto()
    NOT_READY = auto()


class MetaxApplication:
    """Application interface.

    Builds all required parts of the application (DI container, configs, and entrypoints).

    Note:
        Do not forget to run other services' (database etc.) before using this class,
        because it contains entrypoints.
        Always use di container and configs from this class.
        Configuration order manages the `__build` method.

    Example:
        app = MetaxApplication(...)
        with app:
            `run_http_server()`

    """

    def __init__(
        self,
        metax_di_container: MetaxContainer,
        metax_configs: BaseConfigs,
        lock: asyncio.Lock | None = None,
    ) -> None:
        if lock is None:
            self.__lock = asyncio.Lock()
        else:
            self.__lock = lock

        self.__metax_di_container = metax_di_container
        self.__metax_configs = metax_configs
        self.__state: MetaxAppState = MetaxAppState.NOT_READY

    def get_di_container(self) -> MetaxContainer:
        return self.__metax_di_container

    def get_configs(self) -> BaseConfigs:
        return self.__metax_configs

    def __configure_di_container(self) -> None:
        self.__metax_di_container.config.from_pydantic(self.__metax_configs)

    @staticmethod
    def __configure_django_app() -> None:
        import django
        from django.conf import settings

        if not settings.configured:
            settings.configure()
        django.setup()

    async def __run_entrypoints(self) -> None:
        opensearch_async_client = await self.__metax_di_container.opensearch_async_client.async_()
        await run_entrypoint(client=opensearch_async_client)

    async def __init_di_resources(self) -> None:
        init_task = self.__metax_di_container.init_resources()
        if init_task:
            await init_task

    async def __shutdown_di_resources(self) -> None:
        shutdown_task = self.__metax_di_container.shutdown_resources()
        if shutdown_task:
            await shutdown_task

    async def __build(self) -> None:
        init_logger()
        self.__configure_di_container()
        await self.__run_entrypoints()
        await self.__init_di_resources()
        self.__configure_django_app()

    async def __aenter__(self) -> Self:
        async with self.__lock:
            if self.__state is MetaxAppState.NOT_READY:
                await self.__build()
                self.__state = MetaxAppState.READY
                return self
            return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        async with self.__lock:
            if self.__state is MetaxAppState.NOT_READY:
                return
            try:
                await self.__shutdown_di_resources()
            finally:
                # Always mark as NOT_READY even if shutdown fails.
                self.__state = MetaxAppState.NOT_READY


METAX_APPLICATION = MetaxApplication(metax_configs=METAX_CONFIGS, metax_di_container=MetaxContainer())
