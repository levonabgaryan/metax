from __future__ import annotations

from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from config_ import metax_configs
from metax_logger.logger import init_logger

from .patterns_container import PatternsContainer
from .repositories_container import RepositoriesContainer
from .resources import async_opensearch_client_resource


class MetaxContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    opensearch_async_client: providers.Resource[AsyncOpenSearch] = providers.Resource(
        async_opensearch_client_resource,
        host=config.opensearch_host,
        port=config.opensearch_port,
        user=config.opensearch_user,
        password=config.opensearch_password,
        verify_certs=config.opensearch_verify_certs,
    )
    repositories_container: providers.Container[RepositoriesContainer] = providers.Container(
        RepositoriesContainer, opensearch_async_client=opensearch_async_client
    )
    patterns_container: providers.Container[PatternsContainer] = providers.Container(
        PatternsContainer, repositories_container=repositories_container
    )


def _build_metax_container() -> MetaxContainer:
    service_container_ = MetaxContainer()
    service_container_.config.from_pydantic(metax_configs)
    return service_container_


_service_container_singleton: MetaxContainer | None = None


def get_metax_container() -> MetaxContainer:
    global _service_container_singleton
    if _service_container_singleton is None:
        init_logger()
        _service_container_singleton = _build_metax_container()
    return _service_container_singleton


async def init_resources(container: MetaxContainer) -> None:
    init_task = container.init_resources()
    if init_task:
        await init_task


async def shutdown_resources(container: MetaxContainer) -> None:
    shutdown_task = container.shutdown_resources()
    if shutdown_task:
        await shutdown_task
