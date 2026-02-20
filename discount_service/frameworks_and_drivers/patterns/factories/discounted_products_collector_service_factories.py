from dependency_injector import providers

from discount_service.core.application.ports.patterns.factories.discounted_products_collector_service_factory import (
    DiscountedProductsCollectorServiceCreator,
)
from discount_service.core.application.patterns.services.discounted_products_collector import (
    BaseDiscountedProductsCollectorService,
)


class GenericCollectorServiceCreator(DiscountedProductsCollectorServiceCreator):
    def __init__(self, provider: providers.Provider[BaseDiscountedProductsCollectorService]) -> None:
        self.__provider = provider

    async def factory_method(self) -> BaseDiscountedProductsCollectorService:
        return await self.__provider.async_()
