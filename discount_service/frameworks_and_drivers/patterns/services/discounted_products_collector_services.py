import asyncio
from datetime import datetime
from typing import AsyncIterator, override

from discount_service.core.application.ports.services.discounted_products_collector import (
    BaseDiscountedProductsCollectorService,
)
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct

from discount_service.core.domain.entities.retailer_entity.retailer import Retailer
from discount_service.frameworks_and_drivers.scrappers_adapters.scrapper_adapter import ScrapperAdapter


class DiscountedProductsCollectorServiceFromRetailer(BaseDiscountedProductsCollectorService):
    def __init__(self, scrapper_adapter: ScrapperAdapter, retailer: Retailer) -> None:
        self._scrapper_adapter = scrapper_adapter
        self._retailer = retailer

    @override
    async def collect_discounted_products(self, started_time: datetime) -> AsyncIterator[DiscountedProduct]:
        async for discounted_product in self._scrapper_adapter.fetch(
            started_time=started_time, retailer=self._retailer
        ):
            yield discounted_product
            await asyncio.sleep(0)
