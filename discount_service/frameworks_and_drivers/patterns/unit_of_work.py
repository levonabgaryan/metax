from types import TracebackType
from typing import Self

from asgiref.sync import sync_to_async
from django.db import transaction

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.repositories.entites_repositories.category import CategoryRepository
from discount_service.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
)
from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from discount_service.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
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
        self.__committed = False

    async def __aenter__(self) -> Self:
        await sync_to_async(transaction.set_autocommit)(False)
        self.__committed = False
        return await super().__aenter__()

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        try:
            await super().__aexit__(exc_type, exc_val, exc_tb)
        finally:
            await sync_to_async(transaction.set_autocommit)(True)

    async def commit(self) -> None:
        await self.__db_commit()
        self.__committed = True

    async def rollback(self) -> None:
        if not self.__committed:
            try:
                await self.__db_rollback()
            except transaction.TransactionManagementError:
                pass

    @sync_to_async
    def __db_commit(self) -> None:
        transaction.commit()

    @sync_to_async
    def __db_rollback(self) -> None:
        transaction.rollback()
