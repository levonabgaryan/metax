from abc import abstractmethod, ABC

from metax.core.application.commands_handlers.command import Command
from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider


class CommandHandler[GenericCommand: Command](ABC):
    def __init__(self, unit_of_work_provider: IUnitOfWorkProvider, event_bus: EventBus) -> None:
        self._unit_of_work_provider = unit_of_work_provider
        self._event_bus = event_bus

    @abstractmethod
    async def handle_command(self, command: GenericCommand) -> None:
        pass
