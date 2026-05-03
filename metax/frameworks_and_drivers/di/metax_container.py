from __future__ import annotations

from dependency_injector import containers, providers
from opensearchpy import AsyncOpenSearch

from metax.core.application.ddd_patterns.services.category_classifier_service import CategoryClassifierService
from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.backend_patterns.unit_of_work.unit_of_work import AbstractUnitOfWork
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax_configs import BaseConfigs

from .patterns_container import PatternsContainer
from .repositories_container import RepositoriesContainer
from .resources_container import ResourceContainer


class _MetaxContainer(containers.DeclarativeContainer):
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


class MetaxContainer:
    """Contains convenient interface for receiving DI components.

    This class implements Facade design pattern from real di container.
    """

    def __init__(self, metax_configs: BaseConfigs) -> None:
        self.__metax_container = _MetaxContainer()
        self.__metax_container.config.from_pydantic(metax_configs)

    async def init_di_container_resources(self) -> None:
        init_task = self.__metax_container.init_resources()
        if init_task:
            await init_task

    async def shutdown_di_container_resources(self) -> None:
        shutdown_task = self.__metax_container.shutdown_resources()
        if shutdown_task:
            await shutdown_task

    def get_unit_of_work(self) -> AbstractUnitOfWork:
        return self.__metax_container.patterns_container.container.unit_of_work()

    def get_unit_of_work_provider(self) -> IUnitOfWorkProvider:
        return self.__metax_container.patterns_container.container.unit_of_work_provider()

    def get_category_classifier_service(self) -> CategoryClassifierService:
        return self.__metax_container.patterns_container.container.category_classifier_service()

    async def get_event_bus(self) -> EventBus:
        return await self.__metax_container.resources_container.container.event_bus.async_()

    async def get_opensearch_async_client(self) -> AsyncOpenSearch:
        return await self.__metax_container.resources_container.container.opensearch_async_client.async_()

    async def get_discounted_product_read_model_repository(self) -> DiscountedProductReadModelRepository:
        return await self.__metax_container.repositories_container.container.discounted_product_read_model_repository.async_()  # noqa: E501
