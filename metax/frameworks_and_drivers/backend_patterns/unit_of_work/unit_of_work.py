from types import TracebackType
from typing import Self, override

from asgiref.sync import sync_to_async
from django.db import close_old_connections, transaction
from django.db.transaction import Atomic

from metax.core.application.ports.backend_patterns.unit_of_work.unit_of_work import AbstractUnitOfWork
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.category import CategoryRepository
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.retailer import RetailerRepository
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    IDiscountedProductReadModelRepository,
)


class UnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        discounted_product_repo: DiscountedProductRepository,
        category_repo: CategoryRepository,
        retailer_repo: RetailerRepository,
        discounted_product_read_model_repo: IDiscountedProductReadModelRepository,
    ) -> None:
        super().__init__(
            discounted_product_repo=discounted_product_repo,
            category_repo=category_repo,
            retailer_repo=retailer_repo,
            discounted_product_read_model_repo=discounted_product_read_model_repo,
        )
        self.__atomic: Atomic | None = None
        self.__rolled_back = False
        self.__committed = False

    @override
    async def __aenter__(self) -> Self:
        self.__atomic = transaction.atomic()
        await sync_to_async(self.__atomic.__enter__)()
        self.__rolled_back = False
        self.__committed = False
        return self

    @override
    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        if self.__atomic is None:
            return
        try:
            await sync_to_async(self.__atomic.__exit__)(exc_type, exc_val, exc_tb)
        finally:
            await sync_to_async(close_old_connections)()

    @override
    async def commit(self) -> None:
        await sync_to_async(transaction.set_rollback)(False)
        self.__committed = True

    @override
    async def rollback(self) -> None:
        await sync_to_async(transaction.set_rollback)(True)
        self.__rolled_back = True
