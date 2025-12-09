from abc import ABC, abstractmethod
from types import TracebackType
from typing import AsyncIterator, ClassVar, NamedTuple, Self

from backend.core.application.ports.repositories.category import CategoryRepository
from backend.core.application.ports.repositories.discounted_product import DiscountedProductRepository
from backend.core.application.ports.repositories.retailer import RetailerRepository
from backend.core.domain.domain_event import DomainEvent


class Repositories(NamedTuple):
    categories: CategoryRepository
    discounted_products: DiscountedProductRepository
    retailers: RetailerRepository


class UnitOfWork(ABC):
    """
    Abstract base class for the Unit of Work pattern.

    Always use this context manager when working with repositories.
    Always call the commit method manually.

    """

    repositories: ClassVar[Repositories]

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

    async def commit(self) -> None:
        await self._commit()

    @abstractmethod
    async def _commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    async def collect_new_events(self) -> AsyncIterator[DomainEvent]:
        for repo in self.repositories:
            for aggregate in repo.seen:
                while aggregate.has_events:
                    yield aggregate.get_one_event()
