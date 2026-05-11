from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from metax.core.application.event_handlers.category.events import CategoryDeleted, CategoryUpdated
from metax.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from metax.core.application.event_handlers.event import Event
from metax.core.application.event_handlers.retailer.events import RetailerDeleted, RetailerUpdated
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.ddd_patterns.repository.entites_repositories.discounted_product import (
    DiscountedProductRepository,
    DiscountedProductWithRelations,
)
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax.core.application.read_models.discounted_product import (
    DiscountedProductCategoryReadModel,
    DiscountedProductReadModel,
)
from metax_logger.request_id_filter import get_request_id, request_id_scope

logger = logging.getLogger(__name__)


def _expect_event[E: Event](event: Event, typ: type[E]) -> E:
    if isinstance(event, typ):
        return event
    msg = f"expected {typ.__name__}, got {type(event).__name__}"
    raise TypeError(msg)


EventHandler = Callable[[Event], Awaitable[None]]


class _EventBusStop:
    """Sentinel value queued to stop the in-process event worker."""


_EVENT_BUS_STOP = _EventBusStop()


@dataclass(frozen=True, slots=True)
class _QueuedEvent:
    """Event plus request id captured at ``emit`` time (worker runs outside HTTP scope)."""

    event: Event
    request_id: str


type _EventBusQueueItem = _QueuedEvent | _EventBusStop


class EventBus:
    """Dispatches domain ``Event`` instances to registered async handlers."""

    def __init__(
        self,
        unit_of_work_provider: IUnitOfWorkProvider,
        discounted_product_read_model_repo: DiscountedProductReadModelRepository,
    ) -> None:
        self.__unit_of_work_provider = unit_of_work_provider
        self.__discounted_product_read_model_repo = discounted_product_read_model_repo
        self.__handlers: dict[type[Event], tuple[EventHandler, ...]] = {
            CategoryUpdated: (self.__update_category_in_discounted_product_read_models,),
            CategoryDeleted: (self.__delete_category_from_discounted_product_read_models,),
            RetailerUpdated: (self.__update_retailer_in_discounted_product_read_models,),
            RetailerDeleted: (self.__delete_discounted_products_by_retailer_from_read_model,),
            NewDiscountedProductsFromRetailerCollected: (self.__delete_old_discounted_products,),
            OldDiscountedProductsDeleted: (self.__add_new_discounted_products_read_models,),
        }
        self.__queue: asyncio.Queue[_EventBusQueueItem] = asyncio.Queue()
        self.__worker_task: asyncio.Task[None] | None = None

    async def emit(self, event: Event) -> None:
        self.register()
        await self.__queue.put(_QueuedEvent(event=event, request_id=get_request_id()))

    async def emit_and_wait(self, event: Event, timeout_seconds: float = 5.0) -> None:
        # Use this method only for tests.
        await self.emit(event)
        await asyncio.wait_for(self.__queue.join(), timeout=timeout_seconds)

    async def wait_until_idle(self, timeout_seconds: float = 120.0) -> None:
        """Drain the queue (including nested handler emits).

        Call after code paths that ``emit`` without waiting—e.g. TaskIQ tasks or use cases—so
        tests do not finish while the worker still touches the DB or OpenSearch (race with
        pytest-django teardown).

        Note:
            Use only for tests
        """
        self.register()
        await asyncio.wait_for(self.__queue.join(), timeout=timeout_seconds)

    def register(self) -> None:
        """Start the background task which reads events from the queue and runs ``handle``."""
        if self.__worker_task is not None and not self.__worker_task.done():
            return
        self.__worker_task = asyncio.create_task(self.__consume_queue(), name="metax-event-bus")

    async def shutdown(self) -> None:
        """Stops the queue, then stops the background worker."""
        if self.__worker_task is None:
            return
        await self.__queue.join()
        await self.__queue.put(_EVENT_BUS_STOP)
        await self.__worker_task
        self.__worker_task = None

    async def __add_new_discounted_products_read_models(self, event: Event) -> None:
        event_: OldDiscountedProductsDeleted = _expect_event(event, OldDiscountedProductsDeleted)
        logger.info(
            "[Event: %s] | Handler: Sync discount products from repo to read model | Status: STARTED",
            event_.__class__.__name__,
        )
        date_limit = event_.new_discounted_products_creation_date

        uow = await self.__unit_of_work_provider.provide()
        repo: DiscountedProductRepository = uow.discounted_product_repo
        read_model_repo: DiscountedProductReadModelRepository = self.__discounted_product_read_model_repo

        async with uow:
            discounted_products = repo.get_by_created_at(created_at=date_limit)
            await uow.commit()

        read_models_batch: list[DiscountedProductReadModel] = []
        batch_size = 500
        async for dp in discounted_products:
            read_models_batch.append(to_read_model(dp))
            if len(read_models_batch) == batch_size:
                await read_model_repo.add_many(read_models_batch)
                read_models_batch = []

        if read_models_batch:
            await read_model_repo.add_many(read_models_batch)

        await read_model_repo.delete_older_than_and_return_deleted_count(date_limit=date_limit)
        logger.info(
            "[Event: %s] | Handler: Sync discount products from entity repo to read model repo | Status: SUCCESS",
            event_.__class__.__name__,
        )

    async def __consume_queue(self) -> None:
        while True:
            item = await self.__queue.get()
            try:
                if item is _EVENT_BUS_STOP:
                    break
                if isinstance(item, _QueuedEvent):
                    with request_id_scope(item.request_id):
                        await self.__handle(item.event)
            except Exception:
                logger.exception("Unhandled error in event bus worker while processing an event")
            finally:
                self.__queue.task_done()

    async def __delete_old_discounted_products(self, event: Event) -> None:
        event_: NewDiscountedProductsFromRetailerCollected = _expect_event(
            event, NewDiscountedProductsFromRetailerCollected
        )
        logger.info(
            "[Event: %s] | Handler: Delete old discount products from repo | Status: STARTED",
            event_.__class__.__name__,
        )
        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            await uow.discounted_product_repo.delete_older_than_and_return_deleted_count(
                date_limit=event_.new_products_created_date
            )
            await uow.commit()
        logger.info(
            "[Event: %s] | Handler: Delete old discount products from repo | Status: SUCCESS",
            event_.__class__.__name__,
        )
        await self.emit(
            OldDiscountedProductsDeleted(new_discounted_products_creation_date=event_.new_products_created_date)
        )

    async def __handle(self, event: Event) -> None:
        handlers = self.__handlers.get(type(event))
        if not handlers:
            msg = f"No handler for event type {type(event).__name__!r}"
            raise NotImplementedError(msg)
        pending: set[asyncio.Future[None]] = {asyncio.ensure_future(handler(event)) for handler in handlers}
        errors: list[Exception] = []
        while pending:
            done: set[asyncio.Future[None]]
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                try:
                    done_task.result()
                except Exception as error:
                    errors.append(error)
        if errors:
            for handled_error in errors:
                logger.exception(
                    "Event handler failed for %r: %r",
                    type(event).__name__,
                    repr(handled_error),
                )
                msg = f"One or more handlers failed for {type(event).__name__}"
            raise RuntimeError(msg)

    async def __update_category_in_discounted_product_read_models(self, event: Event) -> None:
        event_: CategoryUpdated = _expect_event(event, CategoryUpdated)
        logger.info(
            "[Event: %s] | Handler: Update category in read model | Status: STARTED | Target UUID: [%s]",
            event_.__class__.__name__,
            event_.category_uuid,
        )
        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            updated_category = await uow.category_repo.get_by_uuid(event_.category_uuid)
            await uow.commit()
        dp_read_repo = self.__discounted_product_read_model_repo
        await dp_read_repo.update_categories(dp_read_repo.category_entity_to_read_fragment(updated_category))
        logger.info(
            "[Event: %s] | Handler: Update category in read model | Status: SUCCESS | Target UUID: [%s]",
            event_.__class__.__name__,
            event_.category_uuid,
        )

    async def __update_retailer_in_discounted_product_read_models(self, event: Event) -> None:
        event_: RetailerUpdated = _expect_event(event, RetailerUpdated)
        logger.info(
            "[Event: %s] | Handler: Update retailer in read model | Status: STARTED | Target UUID: [%s]",
            event_.__class__.__name__,
            event_.retailer_uuid,
        )
        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            updated_retailer = await uow.retailer_repo.get_by_uuid(event_.retailer_uuid)
            await uow.commit()
        dp_read_repo = self.__discounted_product_read_model_repo
        await dp_read_repo.update_retailers(dp_read_repo.retailer_entity_to_read_fragment(updated_retailer))

        logger.info(
            "[Event: %s] | Handler: Update retailer in read model | Status: SUCCESS | Target UUID: [%s]",
            event_.__class__.__name__,
            event_.retailer_uuid,
        )

    async def __delete_discounted_products_by_retailer_from_read_model(self, event: Event) -> None:
        event_: RetailerDeleted = _expect_event(event, RetailerDeleted)
        logger.info(
            "[Event: %s] | Handler: Delete discounted products by retailer from read model | Status: STARTED | Target UUID: [%s]",  # noqa: E501
            event_.__class__.__name__,
            event_.retailer_uuid,
        )
        dp_read_repo = self.__discounted_product_read_model_repo
        deleted_count = await dp_read_repo.delete_by_retailer_uuid_and_return_deleted_count(event_.retailer_uuid)
        logger.info(
            "[Event: %s] | Handler: Delete discounted products by retailer from read model | Status: SUCCESS | Target UUID: [%s] | Deleted: [%s]",  # noqa: E501
            event_.__class__.__name__,
            event_.retailer_uuid,
            deleted_count,
        )

    async def __delete_category_from_discounted_product_read_models(self, event: Event) -> None:
        event_: CategoryDeleted = _expect_event(event, CategoryDeleted)
        logger.info(
            "[Event: %s] | Handler: Delete category fragment from read model | Status: STARTED | Target UUID: [%s]",  # noqa: E501
            event_.__class__.__name__,
            event_.category_uuid,
        )
        dp_read_repo = self.__discounted_product_read_model_repo
        updated_count = await dp_read_repo.delete_category_by_category_uuid_and_return_updated_count(
            event_.category_uuid
        )
        logger.info(
            "[Event: %s] | Handler: Delete category fragment from read model | Status: SUCCESS | Target UUID: [%s] | Updated: [%s]",  # noqa: E501
            event_.__class__.__name__,
            event_.category_uuid,
            updated_count,
        )


def to_read_model(discounted_product_with_details: DiscountedProductWithRelations) -> DiscountedProductReadModel:
    entity = discounted_product_with_details.entity
    retailer_entity = discounted_product_with_details.retailer
    created_at = entity.get_created_at().isoformat()
    updated_at = entity.get_updated_at().isoformat()
    result: DiscountedProductReadModel = {
        "uuid_": str(entity.get_uuid()),
        "name": entity.get_name(),
        "real_price": float(entity.get_real_price()),
        "discounted_price": float(entity.get_discounted_price()),
        "created_at": created_at,
        "updated_at": updated_at,
        "url": str(entity.get_url()),
        "retailer": {
            "uuid_": str(retailer_entity.get_uuid()),
            "created_at": retailer_entity.get_created_at().isoformat(),
            "updated_at": retailer_entity.get_updated_at().isoformat(),
            "name": retailer_entity.get_name(),
            "home_page_url": retailer_entity.get_home_page_url(),
            "phone_number": retailer_entity.get_phone_number(),
        },
    }
    category_entity = discounted_product_with_details.category
    if category_entity is not None:
        result["category"] = DiscountedProductCategoryReadModel(
            uuid_=str(category_entity.get_uuid()),
            created_at=category_entity.get_created_at().isoformat(),
            updated_at=category_entity.get_updated_at().isoformat(),
            name=category_entity.get_name(),
        )
    return result
