from dependency_injector import providers, containers

import constants
from discount_service.core.application.patterns.services.discounted_products_collector import (
    BaseDiscountedProductsCollectorService,
)
from discount_service.frameworks_and_drivers.patterns.services.discounted_products_collector_services import (
    DiscountedProductsCollectorService,
)


class DiscountedProductsCollectorServicesContainer(containers.DeclarativeContainer):
    patterns_container: providers.DependenciesContainer = providers.DependenciesContainer()
    scrappers_adapters_container: providers.DependenciesContainer = providers.DependenciesContainer()

    yerevan_city_discounted_products_collector_service: providers.ThreadSafeSingleton[
        BaseDiscountedProductsCollectorService
    ] = providers.ThreadSafeSingleton(
        DiscountedProductsCollectorService,
        unit_of_work=patterns_container.unit_of_work,
        scrapper_adapter=scrappers_adapters_container.yerevan_city_scrapper_adapter,
        retailer_name=constants.RetailersNames.YEREVAN_CITY,
    )

    sas_am_discounted_products_collector_service: providers.ThreadSafeSingleton[
        BaseDiscountedProductsCollectorService
    ] = providers.ThreadSafeSingleton(
        DiscountedProductsCollectorService,
        unit_of_work=patterns_container.unit_of_work,
        scrapper_adapter=scrappers_adapters_container.sas_am_scrapper_adapter,
        retailer_name=constants.RetailersNames.SAS_AM,
    )
