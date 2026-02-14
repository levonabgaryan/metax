from contextlib import asynccontextmanager
from typing import AsyncIterator

from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from discount_service.frameworks_and_drivers.di.commands_handlers_container import CommandsHandlersContainer
from discount_service.frameworks_and_drivers.di.discounted_product_factories_container import (
    DiscountedProductFactoriesContainer,
)
from discount_service.frameworks_and_drivers.di.event_handlers_container import EventHandlersContainer
from discount_service.frameworks_and_drivers.di.patterns_container import PatternsContainer
from discount_service.frameworks_and_drivers.di.repositories_container import RepositoriesContainer
from discount_service.frameworks_and_drivers.di.use_cases_container import UseCasesContainer
from config import discount_service_configs


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
    commands_handlers_container: providers.Container[CommandsHandlersContainer] = providers.Container(
        CommandsHandlersContainer, patterns_container=patterns_container
    )
    event_handlers_container: providers.Container[EventHandlersContainer] = providers.Container(
        EventHandlersContainer, patterns_container=patterns_container
    )
    use_cases_container: providers.Container[UseCasesContainer] = providers.Container(
        UseCasesContainer, patterns_container=patterns_container
    )
    discounted_product_factories_container: providers.Container[DiscountedProductFactoriesContainer] = (
        providers.Container(DiscountedProductFactoriesContainer, repositories_container=repositories_container)
    )


def configured_service_container() -> ServiceContainer:
    service_container_ = ServiceContainer()
    service_container_.config.from_pydantic(discount_service_configs)
    return service_container_
