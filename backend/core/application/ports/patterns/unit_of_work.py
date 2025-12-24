from abc import ABC, abstractmethod
from types import TracebackType
from typing import AsyncIterator, NamedTuple, Self

from backend.core.application.ports.repositories.category import CategoryRepository
from backend.core.application.ports.repositories.discounted_product import DiscountedProductRepository
from backend.core.application.ports.repositories.retailer import RetailerRepository
from backend.core.domain.event import Event


class Repositories(NamedTuple):
    category: CategoryRepository
    discounted_product: DiscountedProductRepository
    retailer: RetailerRepository


class UnitOfWork(ABC):
    """
    Abstract base class for the Unit of Work pattern.

    Always use this context manager when working with repositories.
    Always call the commit method manually.

    """

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

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        """
        Exit the async context manager.

        Rollback is always called after exiting the 'with' statement.
        Since commit must be called manually, rollback does nothing
        if commit has already been executed successfully.
        """
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    async def collect_new_events(self) -> AsyncIterator[Event]:
        for repo in self.repositories:
            for aggregate in repo.seen:
                while aggregate.has_events:
                    yield aggregate.get_one_event()
