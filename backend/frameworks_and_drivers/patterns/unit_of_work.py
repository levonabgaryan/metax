from types import TracebackType
from typing import Self

from asgiref.sync import sync_to_async
from django.db import transaction

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.frameworks_and_drivers.repositories.category import DjangoSqlLiteCategoryRepository
from backend.frameworks_and_drivers.repositories.discounted_product import DjangoSqlLiteDiscountedProductRepository
from backend.frameworks_and_drivers.repositories.retailer import DjangoSqlLiteRetailerRepository


class DjangoUnitOfWork(UnitOfWork):
    def __init__(
        self,
        category_repository: DjangoSqlLiteCategoryRepository,
        retailer_repository: DjangoSqlLiteRetailerRepository,
        discounted_product_repository: DjangoSqlLiteDiscountedProductRepository,
    ) -> None:
        super().__init__(
            category_repository=category_repository,
            retailer_repository=retailer_repository,
            discounted_product_repository=discounted_product_repository,
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
