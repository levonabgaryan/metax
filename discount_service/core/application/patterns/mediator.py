# https://refactoring.guru/design-patterns/mediator
from __future__ import annotations

from abc import ABC, abstractmethod


class Mediator(ABC):
    @abstractmethod
    async def notify(self, sender: MessageHandler, message: Message) -> None:
        pass


class MessageHandler:
    def __init__(self, mediator: Mediator) -> None:
        self.__mediator = mediator

    def get_mediator(self) -> Mediator:
        return self.__mediator

    async def handle(self, message: Message) -> None:
        mediator = self.get_mediator()
        await mediator.notify(sender=self, message=message)


class Message:
    pass
