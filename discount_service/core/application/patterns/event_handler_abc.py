from __future__ import annotations

from abc import ABC, abstractmethod

from discount_service.core.application.patterns.mediator import BaseMessageHandler, Mediator
from discount_service.core.application.patterns.message_bus_1 import Event
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork


class EventHandler(ABC, BaseMessageHandler):
    def __init__(self, mediator: Mediator, unit_of_work: AbstractUnitOfWork) -> None:
        super().__init__(mediator)
        self.__unit_of_work = unit_of_work

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        pass
