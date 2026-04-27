from __future__ import annotations

from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer
from opensearchpy import AsyncOpenSearch

from metax.core.application.event_handlers.event_bus import EventBus
from metax.frameworks_and_drivers.di.resources import (
    async_opensearch_client_resource,
    event_bus_resource,
)


class ResourceContainer(DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()
    patterns_container: providers.DependenciesContainer = providers.DependenciesContainer()
    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()

    opensearch_async_client: providers.Resource[AsyncOpenSearch] = providers.Resource(
        async_opensearch_client_resource,
        host=config.opensearch_host,
        port=config.opensearch_port,
        user=config.opensearch_user,
        password=config.opensearch_password,
        verify_certs=config.opensearch_verify_certs,
    )
    event_bus: providers.Resource[EventBus] = providers.Resource(
        event_bus_resource,
        unit_of_work_provider=patterns_container.unit_of_work_provider,
        discounted_product_read_model_repo=repositories_container.discounted_product_read_model_repository,
    )
