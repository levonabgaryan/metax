from __future__ import annotations
from dependency_injector import containers, providers

from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.patterns.services.category_classifier_service import (
    CategoryClassifierService,
)
from metax.core.application.ports.patterns.factories.unit_of_work_factory import IUnitOfWorkFactory
from metax.core.application.ports.patterns.unit_of_work.unit_of_work import AbstractUnitOfWork
from metax.frameworks_and_drivers.patterns.factories.unit_of_work_factory import DjangoUnitOfWorkFactory
from metax.frameworks_and_drivers.patterns.unit_of_work.unit_of_work import UnitOfWork


class PatternsContainer(containers.DeclarativeContainer):
    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()
    discounted_products_collector_services_container: providers.DependenciesContainer = (
        providers.DependenciesContainer()
    )
    unit_of_work: providers.Factory[AbstractUnitOfWork] = providers.Factory(
        UnitOfWork,
        discounted_product_repo=repositories_container.discounted_product_repository,
        retailer_repo=repositories_container.retailer_repository,
        category_repo=repositories_container.category_repository,
        discounted_product_read_model_repo=repositories_container.discounted_product_read_model_repository,
    )
    unit_of_work_factory: providers.Factory[IUnitOfWorkFactory] = providers.Factory(
        DjangoUnitOfWorkFactory, unit_of_work_provider=unit_of_work.provider
    )
    category_classifier_service: providers.Factory[CategoryClassifierService] = providers.Factory(
        CategoryClassifierService, unit_of_work=unit_of_work
    )
    event_bus: providers.ThreadSafeSingleton[EventBus] = providers.ThreadSafeSingleton(
        EventBus,
        unit_of_work=unit_of_work,
    )
