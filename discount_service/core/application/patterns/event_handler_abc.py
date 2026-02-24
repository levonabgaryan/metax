from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from discount_service.core.application.patterns.message_publisher import MessagePublisher
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.domain.event import GenericEvent


class EventHandler(Generic[GenericEvent], ABC):
    def __init__(self, unit_of_work: AbstractUnitOfWork, message_publisher: MessagePublisher) -> None:
        self.__unit_of_work = unit_of_work
        self.__message_publisher = message_publisher

    @abstractmethod
    async def handle(self, event: GenericEvent) -> None:
        pass
