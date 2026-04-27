from __future__ import annotations

from dependency_injector import containers, providers

from .patterns_container import PatternsContainer
from .repositories_container import RepositoriesContainer
from .resources_container import ResourceContainer


class MetaxContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    resources_container: providers.Container[ResourceContainer] = providers.Container(
        ResourceContainer,
        config=config,
    )
    repositories_container: providers.Container[RepositoriesContainer] = providers.Container(
        RepositoriesContainer,
    )
    patterns_container: providers.Container[PatternsContainer] = providers.Container(
        PatternsContainer,
    )

    resources_container.patterns_container.override(patterns_container)
    resources_container.repositories_container.override(repositories_container)

    repositories_container.resources_container.override(resources_container)

    patterns_container.repositories_container.override(repositories_container)
