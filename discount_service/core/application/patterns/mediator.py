# https://refactoring.guru/design-patterns/mediator
from __future__ import annotations

from abc import ABC, abstractmethod

from discount_service.core.application.patterns.event import Event
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork


class Mediator(ABC):
    @abstractmethod
    async def notify(self, sender: BaseHandler, event: Event) -> None:
        pass


class BaseHandler:
    def __init__(self, unit_of_work: AbstractUnitOfWork, mediator: Mediator | None = None) -> None:
        self.__mediator = mediator
        self._unit_of_work = unit_of_work

    def get_mediator(self) -> Mediator:
        if self.__mediator is None:
            raise AttributeError("Mediator has not been initialized")
        return self.__mediator

    def set_mediator(self, mediator: Mediator) -> None:
        self.__mediator = mediator
