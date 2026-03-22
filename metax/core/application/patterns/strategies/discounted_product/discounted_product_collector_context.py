import asyncio
from datetime import datetime
from typing import AsyncIterator

from metax.core.application.patterns.strategies.discounted_product.discounted_product_collector_strategy import (
    DiscountedProductCollectorStrategy,
)
from metax.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct


class DiscountedProductCollectorContext:
    def __init__(
        self,
        start_date_of_collecting: datetime,
        strategy: DiscountedProductCollectorStrategy | None = None,
    ) -> None:
        self.__strategy = strategy
        self.__start_date_of_collecting = start_date_of_collecting

    def set_strategy(self, strategy: DiscountedProductCollectorStrategy) -> None:
        self.__strategy = strategy

    def get_strategy(self) -> DiscountedProductCollectorStrategy:
        if self.__strategy is None:
            raise AttributeError("Strategy not set")
        return self.__strategy

    async def do_collect(self) -> AsyncIterator[DiscountedProduct]:
        strategy = self.get_strategy()
        async for discounted_product in strategy.collect(start_date_of_collecting=self.__start_date_of_collecting):
            yield discounted_product
            await asyncio.sleep(0)
