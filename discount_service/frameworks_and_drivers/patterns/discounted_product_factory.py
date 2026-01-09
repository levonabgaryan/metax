from datetime import datetime
from typing import AsyncIterator

from discount_service.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct


class DiscountedProductFactory(IDiscountedProductFactory):
    async def create_many_from_retailer(
        self, retailer_url: str, started_time: datetime, batch_size: int = 500
    ) -> AsyncIterator[list[DiscountedProduct]]:
        yield []
