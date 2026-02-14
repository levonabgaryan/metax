from dependency_injector import providers, containers

from discount_service.core.application.ports.patterns.discounted_product_factory import DiscountedProductFactory
from discount_service.frameworks_and_drivers.patterns.factories.discounted_product import (
    YerevanCityDiscountedProductFactory,
)


class DiscountedProductFactoriesContainer(containers.DeclarativeContainer):
    config: providers.Configuration = providers.Configuration()

    repositories_container: providers.DependenciesContainer = providers.DependenciesContainer()

    yerevan_city_discounted_product_factory: providers.ThreadSafeSingleton[DiscountedProductFactory] = (
        providers.ThreadSafeSingleton(
            YerevanCityDiscountedProductFactory,
            retailer_repository=repositories_container.retailer_repository,
            category_repository=repositories_container.category_repository,
            yerevan_city_api_url=config.yerevan_city_api_url,
            yerevan_city_discount_page_url=config.yerevan_city_discount_page_url,
        )
    )
