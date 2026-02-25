from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from config import discount_service_configs


from discount_service.frameworks_and_drivers.di.patterns_container import PatternsContainer
from discount_service.frameworks_and_drivers.di.repositories_container import RepositoriesContainer
from discount_service.frameworks_and_drivers.di.scrappers_adapters_container import ScrappersAdaptersContainer
from discount_service.frameworks_and_drivers.di.scrappers_adapters_selector_container import (
    ScrappersAdaptersSelectorContainer,
)


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


class ServiceContainer(containers.DeclarativeContainer):
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
    scrappers_adapters_container: providers.Container[ScrappersAdaptersContainer] = providers.Container(
        ScrappersAdaptersContainer, config=config
    )
    scrappers_adapters_selector_container: providers.Container[ScrappersAdaptersSelectorContainer] = (
        providers.Container(
            ScrappersAdaptersSelectorContainer, scrappers_adapters_container=scrappers_adapters_container
        )
    )


def configured_service_container() -> ServiceContainer:
    service_container_ = ServiceContainer()
    service_container_.config.from_pydantic(discount_service_configs)
    return service_container_
