from abc import ABC, abstractmethod

from discount_service.core.application.patterns.services.discounted_products_collector import (
    DiscountedProductsCollectorService,
)


class DiscountedProductsCollectorServiceCreator(ABC):
    @abstractmethod
    async def factory_method(self) -> DiscountedProductsCollectorService:
        pass
