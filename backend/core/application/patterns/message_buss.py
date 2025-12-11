import asyncio
import logging
from typing import cast

from backend.core.application.commands_and_handlers.category import (
    CreateCategoryCommand,
    CreateCategoryCommandHandler,
    UpdateCategoryNameCommand,
    UpdateCategoryNameCommandHandler,
)
from backend.core.application.patterns.command import Command
from backend.core.application.patterns.command_handler_abc import CommandHandler, GenericCommand
from backend.core.application.patterns.domain_event_handler_abc import DomainEventHandler
from backend.core.application.patterns.unit_of_work import UnitOfWork
from backend.core.domain.domain_event import DomainEvent, GenericDomainEvent

logger = logging.getLogger(__name__)


class MessageBus:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
    ) -> None:
        self.unit_of_work = unit_of_work
        self.__queue: asyncio.Queue[Command | DomainEvent] = asyncio.Queue()

    async def handle(self, message: Command | DomainEvent) -> None:
        await self.__queue.put(message)

        while not self.__queue.empty():
            message = await self.__queue.get()

            if isinstance(message, DomainEvent):
                await self.handle_event(message)
            elif isinstance(message, Command):
                await self.handle_command(message)

    async def handle_event(self, event: DomainEvent) -> None:
        handler_type: type[DomainEventHandler[DomainEvent]]

        for handler_type in get_domain_event_handlers(event):
            try:
                logger.debug("handling event %s with handler %s", event)
                handler = handler_type(domain_event=event, unit_of_work=self.unit_of_work)  # type: ignore
                await handler.handle(event)
                async for new_event in self.unit_of_work.collect_new_events():
                    await self.__queue.put(new_event)
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    async def handle_command(self, command: Command) -> None:
        logger.debug("handling command %s", command)
        try:
            handler = get_command_handler(command)
            await handler(unit_of_work=self.unit_of_work).handle(command)
            async for new_event in self.unit_of_work.collect_new_events():
                await self.__queue.put(new_event)
        except Exception:
            logger.exception("Exception handling command %s", command)
            raise


def get_command_handler(command: GenericCommand) -> type[CommandHandler[GenericCommand]]:
    command_handlers = {
        CreateCategoryCommand: CreateCategoryCommandHandler,
        UpdateCategoryNameCommand: UpdateCategoryNameCommandHandler,
    }
    command_type = type(command)
    handler_class = command_handlers[command_type]
    return cast(type[CommandHandler[GenericCommand]], handler_class)


def get_domain_event_handlers(event: DomainEvent) -> list[type[DomainEventHandler[GenericDomainEvent]]]:
    event_handlers = {}  # type: ignore
    event_type = type(event)
    handler_classes = event_handlers[event_type]
    return cast(list[type[DomainEventHandler[GenericDomainEvent]]], handler_classes)
