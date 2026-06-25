from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from metax.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from metax.core.application.event_handlers.event import Event
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax_logger.request_id_filter import get_request_id, request_id_scope

logger = logging.getLogger(__name__)

# Embedding hits the embeddings service, which can transiently fail (e.g. a ReadTimeout
# while the model loads into memory on a cold start). ``embed_pending`` is idempotent — it only
# fetches rows whose embedding is still NULL — so retrying simply resumes from wherever it stopped.
_EMBED_MAX_ATTEMPTS = 3
_EMBED_RETRY_BACKOFF_SECONDS = 5.0  # multiplied by the attempt number for a linear backoff


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
        embed_after_collect: bool = True,
    ) -> None:
        self.__unit_of_work_provider = unit_of_work_provider
        self.__discounted_product_read_model_repo = discounted_product_read_model_repo
        self.__embed_after_collect = embed_after_collect
        self.__handlers: dict[type[Event], tuple[EventHandler, ...]] = {
            NewDiscountedProductsFromRetailerCollected: (self.__delete_old_discounted_products,),
            OldDiscountedProductsDeleted: (self.__embed_new_discounted_products,),
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
        tests do not finish while the worker still touches the DB (race with
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

    async def __embed_new_discounted_products(self, event: Event) -> None:
        event_: OldDiscountedProductsDeleted = _expect_event(event, OldDiscountedProductsDeleted)
        if not self.__embed_after_collect:
            logger.info(
                "[Event: %s] | Handler: Embed newly collected discount products | "
                "Status: SKIPPED (EMBED_AFTER_COLLECT=false) | run scripts/backfill_embeddings.py to embed later",
                event_.__class__.__name__,
            )
            return
        logger.info(
            "[Event: %s] | Handler: Embed newly collected discount products | Status: STARTED",
            event_.__class__.__name__,
        )
        embedded_count = await self.__embed_pending_with_retry(event_.__class__.__name__)
        logger.info(
            "[Event: %s] | Handler: Embed newly collected discount products | Status: SUCCESS | Embedded: [%s]",
            event_.__class__.__name__,
            embedded_count,
        )

    async def __embed_pending_with_retry(self, event_name: str) -> int:
        last_error: Exception | None = None
        for attempt in range(1, _EMBED_MAX_ATTEMPTS + 1):
            try:
                return await self.__discounted_product_read_model_repo.embed_pending()
            except Exception as error:
                last_error = error
                if attempt < _EMBED_MAX_ATTEMPTS:
                    backoff = _EMBED_RETRY_BACKOFF_SECONDS * attempt
                    logger.warning(
                        "[Event: %s] | Handler: Embed newly collected discount products | "
                        "Status: RETRY | attempt %d/%d failed (%r); retrying in %.0fs",
                        event_name,
                        attempt,
                        _EMBED_MAX_ATTEMPTS,
                        error,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
        msg = f"Embedding failed after {_EMBED_MAX_ATTEMPTS} attempts"
        raise RuntimeError(msg) from last_error

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
            msg = f"One or more handlers failed for {type(event).__name__}"
            for handled_error in errors:
                logger.exception(
                    "Event handler failed for %r: %r",
                    type(event).__name__,
                    repr(handled_error),
                )
            raise RuntimeError(msg)
