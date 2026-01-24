from contextlib import asynccontextmanager
from typing import AsyncIterator

from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch
from django.conf import settings

from discount_service.frameworks_and_drivers.di.commands_handlers_container import CommandsHandlersContainer
from discount_service.frameworks_and_drivers.di.event_handlers_container import EventHandlersContainer
from discount_service.frameworks_and_drivers.di.patterns_container import PatternsContainer
from discount_service.frameworks_and_drivers.di.use_cases_container import UseCasesContainer
from django_framework.settings.base import OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_AUTH


@asynccontextmanager
async def async_opensearch_client_resource(
    host: str, port: int, http_auth: tuple[str, str], verify_certs: bool
) -> AsyncIterator[AsyncOpenSearch]:
    # https://python-dependency-injector.ets-labs.org/providers/resource.html#:~:text=Asynchronous%20Context%20Manager%20initializer%3A
    client = AsyncOpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=http_auth,
        use_ssl=True,
        verify_certs=verify_certs,
    )
    try:
        yield client
    finally:
        await client.close()


class ServiceContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    opensearch_async_client = providers.Resource(
        async_opensearch_client_resource,
        host=config.opensearch.host,
        port=config.opensearch.port,
        http_auth=config.opensearch.http_auth,
        verify_certs=config.verify_certs,
    )
    patterns_container: providers.Container[PatternsContainer] = providers.Container(
        PatternsContainer, opensearch_async_client=opensearch_async_client
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


def configured_service_container() -> ServiceContainer:
    service_container = ServiceContainer()
    service_container.config.from_dict(
        {
            "opensearch": {
                "host": OPENSEARCH_HOST,
                "port": OPENSEARCH_PORT,
                "http_auth": OPENSEARCH_AUTH,
            },
            "verify_certs": settings.OPENSEARCH_VERIFY_CERTS,
        }
    )
    return service_container
