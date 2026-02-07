import asyncio
from abc import ABC, abstractmethod
from types import TracebackType
from typing import AsyncIterator, Self

from discount_service.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from discount_service.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from discount_service.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)
from discount_service.core.domain.ddd_patterns import AggregateRootEntity
from discount_service.core.domain.event import Event


class AbstractUnitOfWork(ABC):
    def __init__(
        self,
        discounted_product_repo: DiscountedProductRepository,
        category_repo: CategoryRepository,
        retailer_repo: RetailerRepository,
        discounted_product_read_model_repo: IDiscountedProductReadModelRepository,
    ) -> None:
        self.__events_queue: asyncio.Queue[Event] = asyncio.Queue()
        self.discounted_product_repo = discounted_product_repo
        self.category_repo = category_repo
        self.retailer_repo = retailer_repo
        self.discounted_product_read_model_repo = discounted_product_read_model_repo

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
        self.__events_queue.put_nowait(event)

    @property
    def has_events(self) -> bool:
        return not self.__events_queue.empty()

    async def collect_new_events(self) -> AsyncIterator[Event]:
        repos = (self.discounted_product_repo, self.category_repo, self.retailer_repo)
        for repo in repos:
            for aggregate in repo.seen:
                if isinstance(aggregate, AggregateRootEntity):
                    while aggregate.has_events:
                        event = aggregate.get_one_event()
                        await self.__events_queue.put(event)
            repo.seen.clear()

        while not self.__events_queue.empty():
            yield await self.__events_queue.get()
            self.__events_queue.task_done()
