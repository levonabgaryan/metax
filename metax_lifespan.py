from __future__ import annotations

import os
import sys

from entrypoint import run_entrypoint
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer
from metax_configs import BaseConfigs
from metax_logger.logger import init_logger


class MetaxAppLifespanManager:
    """Orchestrates the lifecycle of the Metax application components.

    This manager provides a centralized way to initialize and teardown resources
    required by different entrypoints (HTTP server, Celery workers, CLI tools etc.).
    Since these environments often run in isolated subprocesses, even shared context
    managers aren't always useful. This class allows for manual, explicit
    lifecycle control.
    Key Features:
        - Unification: Serves as a single source of truth for various entrypoints
          including HTTP web servers, Celery workers, and CLI tools.
        - Process Isolation: Designed for environments running via subprocesses
          where standard context managers may not provide a convenient interface.
          It offers explicit methods for manual lifecycle orchestration.
        - Safety: Protects the Dependency Injection (DI) container with
          initialization state checks to prevent access to inactive resources.
    """

    def __init__(
        self,
        metax_configs: BaseConfigs,
        metax_container: MetaxContainer,
    ) -> None:
        self.__metax_di_container = metax_container
        self.__metax_configs = metax_configs

        self.__is_resources_initialized = False

    def configure_django_app(self) -> None:
        import django
        from django.conf import settings

        project_root = self.__metax_configs.project_root_pythonpath
        django_dir = self.__metax_configs.django_dir

        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        if django_dir not in sys.path:
            sys.path.insert(0, django_dir)

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_framework.settings")

        if not settings.configured:
            django.setup(set_prefix=False)
            return
        django.setup()

    def configure_logger(self) -> None:
        init_logger(metax_configs=self.__metax_configs)

    def get_metax_container(self) -> MetaxContainer:
        if not self.__is_resources_initialized:
            msg = "Di container has not been initialized yet"
            raise RuntimeError(msg)
        return self.__metax_di_container

    async def init_metax_container_resources(self) -> None:
        await self.__metax_di_container.init_di_container_resources()
        self.__is_resources_initialized = True

    async def run_entrypoints(self) -> None:
        opensearch_async_client = await self.get_metax_container().get_opensearch_async_client()
        await run_entrypoint(client=opensearch_async_client, metax_configs=self.__metax_configs)

    async def shutdown_metax_container_resources(self) -> None:
        await self.__metax_di_container.shutdown_di_container_resources()
