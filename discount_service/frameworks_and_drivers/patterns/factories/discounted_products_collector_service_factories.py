from dependency_injector import providers

from discount_service.core.application.ports.patterns.factories.discounted_products_collector_service_factory import (
    DiscountedProductsCollectorServiceCreator,
)
from discount_service.core.application.patterns.services.discounted_products_collector import (
    DiscountedProductsCollectorService,
)
from discount_service.frameworks_and_drivers.patterns.services.discounted_products_collector_services import (
    YerevanCityDiscountedProductsCollectorService,
)


class YerevanCityDiscountedProductsCollectorServiceCreator(DiscountedProductsCollectorServiceCreator):
    def __init__(
        self,
        yerevan_city_discounted_products_collector_service_provider: providers.Provider[
            YerevanCityDiscountedProductsCollectorService
        ],
    ) -> None:
        self.__provider = yerevan_city_discounted_products_collector_service_provider

    async def factory_method(self) -> DiscountedProductsCollectorService:
        return await self.__provider.async_()
