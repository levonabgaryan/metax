from abc import abstractmethod

from discount_service.core.application.patterns.command import GenericCommand
from discount_service.core.application.patterns.mediator import BaseHandler


class CommandHandler[GenericCommand](BaseHandler):
    @abstractmethod
    async def handle_command(self, command: GenericCommand) -> None:
        pass
