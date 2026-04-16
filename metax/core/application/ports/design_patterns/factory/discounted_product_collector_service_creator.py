import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from metax.core.application.ports.ddd_patterns.service.discounted_product_collector_service import (
    DiscountedProductCollectorService,
)
from metax.core.domain.entities.discounted_product.entity import DiscountedProduct


class DiscountedProductCollectorServiceCreator(ABC):
    def __init__(
        self,
        start_date_of_collecting: datetime,
    ) -> None:
        self.__start_date_of_collecting = start_date_of_collecting

    @abstractmethod
    def create_collector_service(self) -> DiscountedProductCollectorService:
        pass

    async def do_collect(self) -> AsyncIterator[DiscountedProduct]:
        strategy = self.create_collector_service()
        async for discounted_product in strategy.collect(start_date_of_collecting=self.__start_date_of_collecting):
            yield discounted_product
            await asyncio.sleep(0)
