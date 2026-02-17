import uuid
from datetime import datetime

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.services.discounted_products_collector import (
    DiscountedProductsCollectorService,
)
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer
from discount_service.frameworks_and_drivers.scrappers.yerevan_city_scrapper import YerevanCityScrapperAdapter


class YerevanCityDiscountedProductCollectorService(DiscountedProductsCollectorService):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        scrapper_adapter: YerevanCityScrapperAdapter,
        yerevan_city_retailer: Retailer,
        batch_size_for_saving_discounted_products: int = 500,
    ) -> None:
        super().__init__(unit_of_work=unit_of_work, retailer=yerevan_city_retailer)
        self._scrapper_adapter = scrapper_adapter
        self._batch_size_for_saving_discounted_products = batch_size_for_saving_discounted_products

    async def _run_collect(self, started_time_of_collected: datetime) -> int:
        total_count = 0
        batch = []

        async for dto in self._scrapper_adapter.fetch():
            product = await self._create_discounted_product(
                name=dto["name"],
                real_price=dto["real_price"],
                discounted_price=dto["discounted_price"],
                created_at=started_time_of_collected,
                discounted_product_uuid=uuid.uuid4(),
                retailer_uuid=self._retailer.get_uuid(),
                url=dto["url"],
            )
            batch.append(product)

            if len(batch) >= self._batch_size_for_saving_discounted_products:
                await self._save_batch(batch)
                total_count += len(batch)
                batch = []

        if batch:
            await self._save_batch(batch)
            total_count += len(batch)

        return total_count
