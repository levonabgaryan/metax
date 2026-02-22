# import uuid
# from datetime import datetime
#
# from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
# from discount_service.core.application.patterns.services.discounted_products_collector import (
#     BaseDiscountedProductsCollectorService,
# )
# from discount_service.core.domain.entities.retailer_entity.retailer import Retailer
# from discount_service.frameworks_and_drivers.scrappers.scrapper_abc import ScrapperAdapter
#
#
# class DiscountedProductsCollectorService(BaseDiscountedProductsCollectorService):
#     def __init__(
#         self, unit_of_work: AbstractUnitOfWork, scrapper_adapter: ScrapperAdapter, retailer_name: str
#     ) -> None:
#         super().__init__(unit_of_work=unit_of_work, retailer_name=retailer_name)
#         self._scrapper_adapter = scrapper_adapter
#
#     async def _run_collect(self, started_time_of_collected: datetime, retailer: Retailer) -> int:
#         total_count = 0
#         batch = []
#
#         async for dto in self._scrapper_adapter.fetch():
#             product = await self._create_discounted_product(
#                 name=dto["name"],
#                 real_price=dto["real_price"],
#                 discounted_price=dto["discounted_price"],
#                 created_at=started_time_of_collected,
#                 discounted_product_uuid=uuid.uuid4(),
#                 retailer_uuid=retailer.get_uuid(),
#                 url=dto["url"],
#             )
#             batch.append(product)
#
#             if len(batch) >= self._batch_size_for_saving_discounted_products:
#                 await self._save_batch(batch)
#                 total_count += len(batch)
#                 batch = []
#
#         if batch:
#             await self._save_batch(batch)
#             total_count += len(batch)
#
#         return total_count
