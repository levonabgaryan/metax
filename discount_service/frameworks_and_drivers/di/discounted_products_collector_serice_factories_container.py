from dependency_injector import containers, providers

from discount_service.core.application.patterns.discounted_products_collector_service_factory import (
    DiscountedProductsCollectorServiceCreator,
)
from discount_service.frameworks_and_drivers.patterns.discounted_products_collector_service_factories import (
    YerevanCityDiscountedProductsCollectorServiceCreator,
)


class DiscountedProductsCollectorServiceFactoriesContainer(containers.DeclarativeContainer):
    yerevan_city_discounted_product_collector_service_factory: providers.ThreadSafeSingleton[
        DiscountedProductsCollectorServiceCreator
    ] = providers.ThreadSafeSingleton(YerevanCityDiscountedProductsCollectorServiceCreator)
