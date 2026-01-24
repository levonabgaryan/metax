from abc import ABC, abstractmethod
from typing import TypeVar

from discount_service.core.application.patterns.command import Command
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork

GenericCommand = TypeVar("GenericCommand", bound=Command)


class CommandHandler[GenericCommand](ABC):
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    @abstractmethod
    async def handle(self, command: GenericCommand) -> None:
        pass
