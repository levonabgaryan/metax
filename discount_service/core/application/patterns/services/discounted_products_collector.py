from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import ClassVar
from uuid import UUID

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError

from discount_service.core.domain.entities.category_entity.category import Category
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer
from discount_service.frameworks_and_drivers.patterns.services.errors import RetailerNameIsMissing


class DiscountedProductsCollectorService(ABC):
    RETAILER_NAME: ClassVar[str]

    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
    ) -> None:
        if not getattr(self, "RETAILER_NAME", None):
            raise RetailerNameIsMissing(service_class_name=f"{self.__class__.__name__}")
        self._unit_of_work = unit_of_work
        self._category_map: dict[str, Category] = {}

    async def collect_from_retailer_and_return_collected_count(self, started_time_of_collected: datetime) -> int:
        # Collects discounted products from some retailer sources, save them, and return the number of collected products.
        try:
            retailer_ = await self.__get_retailer_by_name(retailer_name=self.RETAILER_NAME)
        except EntityIsNotFoundError:
            print(f"Collector failed: Retailer with name '{self.RETAILER_NAME}' not found in DB.")
            return 0
        await self._ensure_categories_loaded()
        return await self._run_collect(started_time_of_collected, retailer=retailer_)

    @abstractmethod
    async def _run_collect(self, started_time_of_collected: datetime, retailer: Retailer) -> int:
        pass

    async def _ensure_categories_loaded(self) -> None:
        # Since this service runs once a day, fetching all categories into memory is efficient enough and avoids unnecessary complexity.
        all_categories = await self._unit_of_work.category_repo.get_all()
        self._category_map = {
            word.lower(): category for category in all_categories for word in category.get_helper_words()
        }

    def _classify_category(self, discounted_product_name: str) -> Category | None:
        for word in discounted_product_name.split():
            if word in self._category_map:
                return self._category_map[word]
        return None

    async def _create_discounted_product(
        self,
        discounted_product_uuid: UUID,
        retailer_uuid: UUID,
        real_price: float | str,
        discounted_price: float | str,
        name: str,
        created_at: datetime,
        url: str,
    ) -> DiscountedProduct:
        category = self._classify_category(discounted_product_name=name)
        price_details = PriceDetails(
            real_price=Decimal(str(real_price)),
            discounted_price=Decimal(str(discounted_price)),
        )
        discounted_product = DiscountedProduct(
            price_details=price_details,
            name=name,
            created_at=created_at,
            category_uuid=category.get_uuid() if category else None,
            retailer_uuid=retailer_uuid,
            discounted_product_uuid=discounted_product_uuid,
            url=url,
        )
        return discounted_product

    async def _save_batch(self, batch: list[DiscountedProduct]) -> None:
        async with self._unit_of_work as uow:
            await uow.discounted_product_repo.add_many(batch)
            await uow.commit()

    async def __get_retailer_by_name(self, retailer_name: str) -> Retailer:
        return await self._unit_of_work.retailer_repo.get_by_name(retailer_name=retailer_name)
