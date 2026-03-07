from types import TracebackType
from typing import Self, override

from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.transaction import Atomic

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
        self._atomic: Atomic | None = None
        self._rolled_back = False
        self._committed = False

    @override
    async def __aenter__(self) -> Self:
        self._atomic = transaction.atomic()
        await sync_to_async(self._atomic.__enter__)()
        self._rolled_back = False
        self._committed = False
        return self

    @override
    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        if self._atomic is None:
            return

        if self._rolled_back and exc_type is None:
            exc_type = RuntimeError
            exc_val = RuntimeError("Rolled back manually")
        await sync_to_async(self._atomic.__exit__)(exc_type, exc_val, exc_tb)

    @override
    async def commit(self) -> None:
        await sync_to_async(transaction.set_rollback)(False)
        self._committed = True

    @override
    async def rollback(self) -> None:
        await sync_to_async(transaction.set_rollback)(True)
        self._rolled_back = True
