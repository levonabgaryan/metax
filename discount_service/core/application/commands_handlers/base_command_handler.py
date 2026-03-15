from abc import abstractmethod, ABC

from discount_service.core.application.commands_handlers.command import Command
from discount_service.core.application.event_handlers.event_bus import EventBus
from discount_service.core.application.ports.patterns.unit_of_work.unit_of_work import AbstractUnitOfWork


class CommandHandler[GenericCommand: Command](ABC):
    def __init__(self, unit_of_work: AbstractUnitOfWork, event_bus: EventBus) -> None:
        self._unit_of_work = unit_of_work
        self._event_bus = event_bus

    @abstractmethod
    async def handle_command(self, command: GenericCommand) -> None:
        pass
