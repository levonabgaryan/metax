# https://refactoring.guru/design-patterns/mediator
from __future__ import annotations

from abc import ABC, abstractmethod


class Mediator(ABC):
    @abstractmethod
    async def notify(self, sender: BaseMessageHandler, message: Message) -> None:
        pass


class BaseMessageHandler(ABC):
    def __init__(self, mediator: Mediator) -> None:
        self.__mediator = mediator

    def get_mediator(self) -> Mediator:
        return self.__mediator


class Message:
    pass
