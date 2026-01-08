import asyncio
import logging
from typing import cast

from discount_service.core.application.commands_and_handlers.cud.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
    UpdateCategoryCommand,
    UpdateCategoryCommandHandler,
)
from discount_service.core.application.commands_and_handlers.cud.retailer import (
    CreateRetailerCommandHandler,
    CreateRetailerCommand,
    UpdateRetailerCommand,
    UpdateRetailerCommandHandler,
)
from discount_service.core.application.event_and_handlers.category.update_in_discounted_product_read_model import (
    UpdateCategoryInDiscountedProductReadModel,
)
from discount_service.core.application.event_and_handlers.discounted_product.delete_old_discounted_products import (
    DeleteOldDiscountedProducts,
)
from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from discount_service.core.application.event_and_handlers.discounted_product.sync_discounted_products_read_model import (
    SyncDiscountedProductReadModel,
)
from discount_service.core.application.event_and_handlers.retailer.update_in_discounted_product_read_model import (
    UpdateRetailerInDiscountedProductReadModel,
)
from discount_service.core.application.patterns.command import Command
from discount_service.core.application.patterns.command_handler_abc import CommandHandler, GenericCommand
from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.application.ports.patterns.unit_of_work_factory import IUnitOfWorkFactory
from discount_service.core.application.ports.patterns.unit_of_work import UnitOfWork
from discount_service.core.domain.entities.category_entity.events import CategoryUpdated
from discount_service.core.domain.entities.retailer_entity.events import RetailerUpdated
from discount_service.core.domain.event import Event, GenericEvent

logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(
        self,
        unit_of_work_factory: IUnitOfWorkFactory,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory

    async def handle(self, message: Command | Event) -> None:
        queue: asyncio.Queue[Command | Event] = asyncio.Queue()
        uow = self.create_unit_of_work()
        await queue.put(message)

        while not queue.empty():
            message = await queue.get()

            if isinstance(message, Event):
                await self.handle_event(message, unit_of_work=uow, queue=queue)
            elif isinstance(message, Command):
                await self.handle_command(message, unit_of_work=uow, queue=queue)

    @staticmethod
    async def handle_event(event: Event, unit_of_work: UnitOfWork, queue: asyncio.Queue[Event | Command]) -> None:
        handler_type: type[EventHandler[Event]]

        for handler_type in get_event_handlers(event):
            try:
                logger.debug("handling event %s with handler %s", event)
                handler = handler_type(unit_of_work=unit_of_work)
                await handler.handle(event)
                async for new_event in unit_of_work.collect_new_events():
                    await queue.put(new_event)
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    @staticmethod
    async def handle_command(
        command: Command, unit_of_work: UnitOfWork, queue: asyncio.Queue[Command | Event]
    ) -> None:
        logger.debug("handling command %s", command)
        try:
            handler = get_command_handler(command)
            await handler(unit_of_work=unit_of_work).handle(command)
            async for new_event in unit_of_work.collect_new_events():
                await queue.put(new_event)
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise

    def create_unit_of_work(self) -> UnitOfWork:
        return self.unit_of_work_factory.create()


def get_command_handler(command: GenericCommand) -> type[CommandHandler[GenericCommand]]:
    commands_handlers = {
        CreateCategoryCommand: CreateCategoryCommandHandler,
        UpdateCategoryCommand: UpdateCategoryCommandHandler,
        CreateRetailerCommand: CreateRetailerCommandHandler,
        UpdateRetailerCommand: UpdateRetailerCommandHandler,
    }
    command_type = type(command)
    handler_class = commands_handlers[command_type]
    return cast(type[CommandHandler[GenericCommand]], handler_class)


def get_event_handlers(event: GenericEvent) -> list[type[EventHandler[GenericEvent]]]:
    event_handlers = {
        NewDiscountedProductsFromRetailerCollected: [DeleteOldDiscountedProducts],
        OldDiscountedProductsDeleted: [SyncDiscountedProductReadModel],
        CategoryUpdated: [UpdateCategoryInDiscountedProductReadModel],
        RetailerUpdated: [UpdateRetailerInDiscountedProductReadModel],
    }
    event_type = type(event)
    handler_classes = event_handlers[event_type]
    return cast(list[type[EventHandler[GenericEvent]]], handler_classes)
