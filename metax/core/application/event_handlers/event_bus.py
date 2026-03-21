from __future__ import annotations

import logging
from functools import singledispatchmethod

from metax.core.application.event_handlers.category.events import CategoryUpdated
from metax.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from metax.core.application.event_handlers.retailer.events import RetailerUpdated
from metax.core.application.event_handlers.event import Event
from metax.core.application.ports.patterns.unit_of_work.unit_of_work import AbstractUnitOfWork
from metax.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
    DiscountedProductWithDetails,
)
from metax.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self.__unit_of_work = unit_of_work

    @singledispatchmethod
    async def handle(self, event: Event) -> None:
        raise NotImplementedError("No handler for this event type")

    # Events handlers
    @handle.register
    async def _(self, event: CategoryUpdated) -> None:
        logger.info(
            "[Event: %s] | Handler: Update category in read model | Status: STARTED | Target UUID: [%s]",
            event.__class__.__name__,
            event.category_uuid,
        )
        updated_category = await self.__unit_of_work.category_repo.get_by_uuid(event.category_uuid)
        await self.__unit_of_work.discounted_product_read_model_repo.update_category(updated_category)
        logger.info(
            "[Event: %s] | Handler: Update category in read model | Status: SUCCESS | Target UUID: [%s]",
            event.__class__.__name__,
            event.category_uuid,
        )

    @handle.register
    async def _(self, event: RetailerUpdated) -> None:
        logger.info(
            "[Event: %s] | Handler: Update retailer in read model | Status: STARTED | Target UUID: [%s]",
            event.__class__.__name__,
            event.retailer_uuid,
        )
        updated_retailer = await self.__unit_of_work.retailer_repo.get_by_uuid(event.retailer_uuid)
        await self.__unit_of_work.discounted_product_read_model_repo.update_retailer(updated_retailer)
        logger.info(
            "[Event: %s] | Handler: Update retailer in read model | Status: SUCCESS | Target UUID: [%s]",
            event.__class__.__name__,
            event.retailer_uuid,
        )

    @handle.register
    async def _(self, event: NewDiscountedProductsFromRetailerCollected) -> None:
        logger.info(
            "[Event: %s] | Handler: Delete old discount products from repo | Status: STARTED",
            event.__class__.__name__,
        )
        await self.__unit_of_work.discounted_product_repo.delete_older_than_and_return_deleted_count(
            date_limit=event.new_products_created_date
        )
        logger.info(
            "[Event: %s] | Handler: Delete old discount products from repo | Status: SUCCESS",
            event.__class__.__name__,
        )
        await self.handle(
            OldDiscountedProductsDeleted(new_discounted_products_creation_date=event.new_products_created_date)
        )

    @handle.register
    async def _(self, event: OldDiscountedProductsDeleted) -> None:
        logger.info(
            "[Event: %s] | Handler: Sync discount products from repo to read model | Status: STARTED",
            event.__class__.__name__,
        )
        batch_size = 500
        current_batch = []
        date_limit = event.new_discounted_products_creation_date

        repo: DiscountedProductRepository = self.__unit_of_work.discounted_product_repo
        read_model_repo: IDiscountedProductReadModelRepository = (
            self.__unit_of_work.discounted_product_read_model_repo
        )

        discounted_product: DiscountedProductWithDetails
        async for discounted_product in repo.get_all_by_date(date_=date_limit):
            current_batch.append(discounted_product)

            if len(current_batch) >= batch_size:
                await read_model_repo.add_many([to_read_model(p) for p in current_batch])
                current_batch.clear()

        if current_batch:
            await read_model_repo.add_many([to_read_model(p) for p in current_batch])

        await read_model_repo.delete_older_than_and_return_deleted_count(date_limit=date_limit)
        logger.info(
            "[Event: %s] | Handler: Sync discount products from repo to read model | Status: SUCCESS",
            event.__class__.__name__,
        )


def to_read_model(discounted_product_with_details: DiscountedProductWithDetails) -> DiscountedProductReadModel:
    return DiscountedProductReadModel(
        discounted_product_uuid=str(discounted_product_with_details.entity.get_uuid()),
        name=discounted_product_with_details.entity.get_name(),
        real_price=float(discounted_product_with_details.entity.get_real_price()),
        discounted_price=float(discounted_product_with_details.entity.get_discounted_price()),
        category_uuid=str(discounted_product_with_details.entity.get_category_uuid())
        if discounted_product_with_details.entity.has_category()
        else None,
        category_name=str(discounted_product_with_details.category_name)
        if discounted_product_with_details.entity.has_category()
        else None,
        retailer_uuid=str(discounted_product_with_details.entity.get_retailer_uuid()),
        retailer_name=str(discounted_product_with_details.retailer_name),
        url=str(discounted_product_with_details.entity.get_url()),
        created_at=discounted_product_with_details.entity.get_created_at().isoformat(),
    )
