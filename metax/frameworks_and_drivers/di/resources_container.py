from __future__ import annotations

from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from metax.core.application.ddd_patterns.services.embedding_category_classifier_service import (
    EmbeddingCategoryClassifierService,
)
from metax.core.application.ddd_patterns.services.embedding_http_service import HttpEmbeddingService
from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.ddd_patterns.service.category_classifier_service import (
    CategoryClassifierService,
)
from metax.core.application.ports.ddd_patterns.service.embedding_service import EmbeddingService
from metax.frameworks_and_drivers.di.resources import (
    event_bus_resource,
)


class ResourceContainer(DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()
    patterns_container: providers.DependenciesContainer = providers.DependenciesContainer()
    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()

    embedding_service: providers.Provider[EmbeddingService] = providers.Singleton(
        HttpEmbeddingService,
        host=config.embedding_host,
        dimensions=config.embedding_dim,
        concurrency=config.embedding_concurrency,
        timeout=config.embedding_timeout,
    )
    category_classifier_service: providers.Provider[CategoryClassifierService] = providers.Singleton(
        EmbeddingCategoryClassifierService,
        embedding_service=embedding_service,
        max_distance=config.category_match_max_distance,
    )
    event_bus: providers.Resource[EventBus] = providers.Resource(
        event_bus_resource,
        unit_of_work_provider=patterns_container.unit_of_work_provider,
    )
