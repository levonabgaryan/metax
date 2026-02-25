from __future__ import annotations
import asyncio
import logging
from typing import cast

from discount_service.core.application.commands_and_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
    UpdateCategoryCommand,
    UpdateCategoryCommandHandler,
)
from discount_service.core.application.commands_and_handlers.retailer import (
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
from discount_service.core.application.event_and_handlers.category.events import CategoryUpdated
from discount_service.core.application.event_and_handlers.retailer.events import RetailerUpdated
from discount_service.core.domain.event import Event, GenericEvent

logger = logging.getLogger(__name__)


Message = Event | Command


class MessageBus:
    # https://refactoring.guru/design-patterns/mediator
    async def handle(self, message: Message) -> None:
        queue: asyncio.Queue[Message] = asyncio.Queue()
        await queue.put(message)

        while not queue.empty():
            message = await queue.get()

            if isinstance(message, Event):
                await self.__handle_event(message)
            elif isinstance(message, Command):
                await self.__handle_command(message)

    async def __handle_event(
        self,
        event: Event,
    ) -> None:
        handler_type: type[EventHandler[Event]]

        for handler_type in self.get_event_handlers(event):
            try:
                logger.debug("handling event %s with handler %s", event)
                handler = handler_type()
                await handler.handle(event)
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    async def __handle_command(
        self,
        command: Command,
    ) -> None:
        logger.debug("handling command %s", command)
        try:
            handler = self.get_command_handler(command)
            await handler().handle(command)
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    async def handle_(message_handler, message: Message) -> None:
        queue: asyncio.Queue[Message] = asyncio.Queue()
        await queue.put(message)

        while not queue.empty():
            message = await queue.get()

            if isinstance(message, Event):
                await message_handler.handle(message)
            elif isinstance(message, Command):
                await message_handler.handle(message)
