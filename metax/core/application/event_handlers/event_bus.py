from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from metax.core.application.event_handlers.event import Event
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax_logger.request_id_filter import get_request_id, request_id_scope

logger = logging.getLogger(__name__)


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
    ) -> None:
        self.__unit_of_work_provider = unit_of_work_provider
        # No domain events are currently dispatched through the bus — collection now wipes/refreshes
        # synchronously in the TaskIQ pipeline. The bus is kept as the seam for future async handlers.
        self.__handlers: dict[type[Event], tuple[EventHandler, ...]] = {}
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

        Call after code paths that ``emit`` without waiting—e.g. the TaskIQ collection task—so the
        caller blocks until the worker has finished processing the delete-old side effect instead of
        returning mid-cleanup. Also used by tests to avoid the worker racing pytest-django teardown.
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
