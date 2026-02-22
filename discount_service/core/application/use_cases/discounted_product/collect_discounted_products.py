from discount_service.core.application.patterns.category_classifier_service import CategoryClassifierService
from discount_service.core.application.ports.patterns.services.discounted_products_collector import (
    BaseDiscountedProductsCollectorService,
)
from discount_service.core.application.patterns.use_case_abc import UseCase
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork

from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsRequest,
    CollectDiscountedProductsResponse,
)
from discount_service.core.domain.entities.category_entity.category import Category
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct


class CollectDiscountedProducts(UseCase[CollectDiscountedProductsRequest, CollectDiscountedProductsResponse]):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        discounted_product_collector_service: BaseDiscountedProductsCollectorService,
        category_classifier_service: CategoryClassifierService,
        batch_size_for_saving_discounted_products: int = 500,
    ) -> None:
        super().__init__(unit_of_work=unit_of_work)
        self.discounted_product_collector_service = discounted_product_collector_service
        self._batch_size_for_saving_discounted_products = batch_size_for_saving_discounted_products
        self._category_map: dict[str, Category] | None = None
        self.__category_classifier_service = category_classifier_service

    async def execute(self, request: CollectDiscountedProductsRequest) -> CollectDiscountedProductsResponse:

        total_count = 0
        batch = []

        async for discounted_product in self.discounted_product_collector_service.collect_discounted_products(
            started_time=request.started_time
        ):
            category = await self.__category_classifier_service.classify_category(discounted_product_name=discounted_product.get_name())
            if category is not None:
                discounted_product.set_category_uuid(category_uuid=category.get_uuid())
            batch.append(discounted_product)

            if len(batch) >= self._batch_size_for_saving_discounted_products:
                await self._save_batch(batch)
                total_count += len(batch)
                batch = []

        if batch:
            await self._save_batch(batch)
            total_count += len(batch)

        return CollectDiscountedProductsResponse(added_count=total_count)

    async def _save_batch(self, batch: list[DiscountedProduct]) -> None:
        async with self.unit_of_work as uow:
            await uow.discounted_product_repo.add_many(batch)
            await uow.commit()
