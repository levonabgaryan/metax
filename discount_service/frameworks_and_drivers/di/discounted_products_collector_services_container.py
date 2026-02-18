from dependency_injector import providers, containers

from discount_service.core.application.services.discounted_products_collector import (
    DiscountedProductsCollectorService,
)
from discount_service.frameworks_and_drivers.services.discounted_products_collectors import (
    YerevanCityDiscountedProductsCollectorService,
)


class DiscountedProductsCollectorServicesContainer(containers.DeclarativeContainer):
    patterns_container: providers.DependenciesContainer = providers.DependenciesContainer()
    scrappers_adapters_container: providers.DependenciesContainer = providers.DependenciesContainer()

    yerevan_city_discounted_products_collector_service: providers.ThreadSafeSingleton[
        DiscountedProductsCollectorService
    ] = providers.ThreadSafeSingleton(
        YerevanCityDiscountedProductsCollectorService,
        unit_of_work=patterns_container.unit_of_work,
        yerevan_city_scrapper_adapter=scrappers_adapters_container.yerevan_city_scrapper_adapter,
    )
