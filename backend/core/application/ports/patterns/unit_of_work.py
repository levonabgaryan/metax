import asyncio
from abc import ABC, abstractmethod
from types import TracebackType
from typing import AsyncIterator, NamedTuple, Self

from backend.core.application.ports.repositories.category import CategoryRepository
from backend.core.application.ports.repositories.discounted_product import DiscountedProductRepository
from backend.core.application.ports.repositories.retailer import RetailerRepository
from backend.core.domain.ddd_patterns import AggregateRootEntity
from backend.core.domain.event import Event


class Repositories(NamedTuple):
    category: CategoryRepository
    discounted_product: DiscountedProductRepository
    retailer: RetailerRepository


class UnitOfWork(ABC):
    def __init__(
        self,
        category_repository: CategoryRepository,
        discounted_product_repository: DiscountedProductRepository,
        retailer_repository: RetailerRepository,
    ):
        self.repositories = Repositories(
            category=category_repository,
            discounted_product=discounted_product_repository,
            retailer=retailer_repository,
        )
        self._events_queue: asyncio.Queue[Event] = asyncio.Queue()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    def add_event(self, event: Event) -> None:
        self._events_queue.put_nowait(event)

    @property
    def has_events(self) -> bool:
        return not self._events_queue.empty()

    async def collect_new_events(self) -> AsyncIterator[Event]:
        for repo in self.repositories:
            for aggregate in repo.seen:
                if isinstance(aggregate, AggregateRootEntity):
                    while aggregate.has_events:
                        event = aggregate.get_one_event()
                        await self._events_queue.put(event)
            repo.seen.clear()

        while not self._events_queue.empty():
            yield await self._events_queue.get()
            self._events_queue.task_done()
