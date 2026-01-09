from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.domain.event import GenericEvent


class EventHandler(Generic[GenericEvent], ABC):
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    @abstractmethod
    async def handle(self, event: GenericEvent) -> None:
        pass
