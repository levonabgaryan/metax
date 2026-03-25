from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from config_ import metax_configs


from metax.frameworks_and_drivers.di.patterns_container import PatternsContainer
from metax.frameworks_and_drivers.di.repositories_container import RepositoriesContainer
from logger.logger import init_logger


@asynccontextmanager
async def async_opensearch_client_resource(
    host: str, port: int, user: str, password: str, verify_certs: bool
) -> AsyncIterator[AsyncOpenSearch]:
    # https://python-dependency-injector.ets-labs.org/providers/resource.html#:~:text=Asynchronous%20Context%20Manager%20initializer%3A
    client = AsyncOpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(user, password),
        use_ssl=True,
        verify_certs=verify_certs,
    )
    try:
        yield client
    finally:
        await client.close()


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
    init_logger()
    service_container_ = MetaxContainer()
    service_container_.config.from_pydantic(metax_configs)
    return service_container_


_service_container_singleton: MetaxContainer | None = None


def get_metax_container() -> MetaxContainer:
    global _service_container_singleton
    if _service_container_singleton is None:
        _service_container_singleton = _build_metax_container()
    return _service_container_singleton
