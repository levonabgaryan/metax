from dependency_injector import containers, providers

from discount_service.core.application.patterns.discounted_products_collector_service_factory import (
    DiscountedProductsCollectorServiceCreator,
)
from discount_service.core.application.patterns.message_buss import MessageBus
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.patterns.unit_of_work_factory import IUnitOfWorkFactory
from discount_service.frameworks_and_drivers.patterns.discounted_products_collector_service_factories import (
    YerevanCityDiscountedProductsCollectorServiceCreator,
)
from discount_service.frameworks_and_drivers.patterns.unit_of_work import UnitOfWork
from discount_service.frameworks_and_drivers.patterns.unit_of_work_factory import DjangoUnitOfWorkFactory


class PatternsContainer(containers.DeclarativeContainer):
    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()
    discounted_products_collector_services_container: providers.DependenciesContainer = (
        providers.DependenciesContainer()
    )

    unit_of_work: providers.Provider[AbstractUnitOfWork] = providers.Factory(
        UnitOfWork,
        discounted_product_repo=repositories_container.discounted_product_repository,
        retailer_repo=repositories_container.retailer_repository,
        category_repo=repositories_container.category_repository,
        discounted_product_read_model_repo=repositories_container.discounted_product_read_model_repository,
    )

    unit_of_work_factory: providers.Provider[IUnitOfWorkFactory] = providers.Factory(
        DjangoUnitOfWorkFactory, unit_of_work_provider=unit_of_work.provider
    )

    message_bus: providers.Provider[MessageBus] = providers.ThreadSafeSingleton(MessageBus, unit_of_work_factory)

    yerevan_city_discounted_products_collector_service_factory: providers.ThreadSafeSingleton[
        DiscountedProductsCollectorServiceCreator
    ] = providers.ThreadSafeSingleton(
        YerevanCityDiscountedProductsCollectorServiceCreator,
        yerevan_city_discounted_products_collector_service_provider=discounted_products_collector_services_container.yerevan_city_discounted_products_collector_service.provider,
    )
