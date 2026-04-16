from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from metax.core.application.event_handlers.category.events import CategoryUpdated
from metax.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from metax.core.application.event_handlers.event import Event
from metax.core.application.event_handlers.retailer.events import RetailerUpdated
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.discounted_product import (
    DiscountedProductRepository,
    DiscountedProductWithDetails,
)
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    IDiscountedProductReadModelRepository,
)
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.core.domain.ddd_patterns.general_value_objects import UUIDValueObject

logger = logging.getLogger(__name__)

_E = TypeVar("_E", bound=Event)


def _expect_event(event: Event, typ: type[_E]) -> _E:
    if isinstance(event, typ):
        return event
    msg = f"expected {typ.__name__}, got {type(event).__name__}"
    raise TypeError(msg)


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    def __init__(
        self,
        unit_of_work_provider: IUnitOfWorkProvider,
        discounted_product_read_model_repo: IDiscountedProductReadModelRepository,
    ) -> None:
        self.__unit_of_work_provider = unit_of_work_provider
        self.__discounted_product_read_model_repo = discounted_product_read_model_repo
        self.__handlers: dict[type[Event], tuple[EventHandler, ...]] = {
            CategoryUpdated: (self._handle_category_updated,),
            RetailerUpdated: (self._handle_retailer_updated,),
            NewDiscountedProductsFromRetailerCollected: (self._handle_new_discounted_products_collected,),
            OldDiscountedProductsDeleted: (self._handle_old_discounted_products_deleted,),
        }

    async def handle(self, event: Event) -> None:
        handlers = self.__handlers.get(type(event))
        if not handlers:
            msg = f"No handler for event type {type(event).__name__!r}"
            raise NotImplementedError(msg)
        # Handlers for the same event type run concurrently,
        # each should use its own UoW and not rely on peer order.
        await asyncio.gather(*(handler(event) for handler in handlers), return_exceptions=True)

    async def _handle_category_updated(self, event: Event) -> None:
        event = _expect_event(event, CategoryUpdated)
        logger.info(
            "[Event: %s] | Handler: Update category in read model | Status: STARTED | Target UUID: [%s]",
            event.__class__.__name__,
            event.category_uuid,
        )
        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            updated_category = await uow.category_repo.get_by_uuid(UUIDValueObject.create(event.category_uuid))
            await self.__discounted_product_read_model_repo.update_category(updated_category)
            await uow.commit()
        logger.info(
            "[Event: %s] | Handler: Update category in read model | Status: SUCCESS | Target UUID: [%s]",
            event.__class__.__name__,
            event.category_uuid,
        )

    async def _handle_retailer_updated(self, event: Event) -> None:
        event = _expect_event(event, RetailerUpdated)
        logger.info(
            "[Event: %s] | Handler: Update retailer in read model | Status: STARTED | Target UUID: [%s]",
            event.__class__.__name__,
            event.retailer_uuid,
        )
        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            updated_retailer = await uow.retailer_repo.get_by_uuid(UUIDValueObject.create(event.retailer_uuid))
            await self.__discounted_product_read_model_repo.update_retailer(updated_retailer)
            await uow.commit()
        logger.info(
            "[Event: %s] | Handler: Update retailer in read model | Status: SUCCESS | Target UUID: [%s]",
            event.__class__.__name__,
            event.retailer_uuid,
        )

    async def _handle_new_discounted_products_collected(self, event: Event) -> None:
        event = _expect_event(event, NewDiscountedProductsFromRetailerCollected)
        logger.info(
            "[Event: %s] | Handler: Delete old discount products from repo | Status: STARTED",
            event.__class__.__name__,
        )
        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            await uow.discounted_product_repo.delete_older_than_and_return_deleted_count(
                date_limit=event.new_products_created_date
            )
            await uow.commit()
        logger.info(
            "[Event: %s] | Handler: Delete old discount products from repo | Status: SUCCESS",
            event.__class__.__name__,
        )
        await self.handle(
            OldDiscountedProductsDeleted(new_discounted_products_creation_date=event.new_products_created_date)
        )

    async def _handle_old_discounted_products_deleted(self, event: Event) -> None:
        event = _expect_event(event, OldDiscountedProductsDeleted)
        logger.info(
            "[Event: %s] | Handler: Sync discount products from repo to read model | Status: STARTED",
            event.__class__.__name__,
        )
        batch_size = 500
        current_batch = []
        date_limit = event.new_discounted_products_creation_date

        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            repo: DiscountedProductRepository = uow.discounted_product_repo
            read_model_repo: IDiscountedProductReadModelRepository = self.__discounted_product_read_model_repo

            discounted_product: DiscountedProductWithDetails
            async for discounted_product in repo.get_all_by_date(date_=date_limit):
                current_batch.append(discounted_product)

                if len(current_batch) >= batch_size:
                    await read_model_repo.add_many([to_read_model(p) for p in current_batch])
                    current_batch.clear()

            if current_batch:
                await read_model_repo.add_many([to_read_model(p) for p in current_batch])

            await read_model_repo.delete_older_than_and_return_deleted_count(date_limit=date_limit)
            await uow.commit()
        logger.info(
            "[Event: %s] | Handler: Sync discount products from repo to read model | Status: SUCCESS",
            event.__class__.__name__,
        )


def to_read_model(discounted_product_with_details: DiscountedProductWithDetails) -> DiscountedProductReadModel:
    return DiscountedProductReadModel(
        uuid_=str(discounted_product_with_details.entity.get_uuid()),
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
