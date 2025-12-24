from typing import AsyncIterator

from backend.core.application.input_ports.patterns.discounted_product_factory import IDiscountedProductFactory
from backend.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct


class DiscountedProductFactory(IDiscountedProductFactory):
    async def create_many_from_retailer(
        self, retailer_url: str, batch_size: int = 500
    ) -> AsyncIterator[list[DiscountedProduct]]:
        yield []
