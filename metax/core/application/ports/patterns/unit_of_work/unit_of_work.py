from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from metax.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from metax.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from metax.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from metax.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)


class AbstractUnitOfWork(ABC):
    def __init__(
        self,
        discounted_product_repo: DiscountedProductRepository,
        category_repo: CategoryRepository,
        retailer_repo: RetailerRepository,
        discounted_product_read_model_repo: IDiscountedProductReadModelRepository,
    ) -> None:
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
