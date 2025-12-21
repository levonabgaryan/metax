from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.domain.event import GenericEvent


class EventHandler(Generic[GenericEvent], ABC):
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    @abstractmethod
    async def handle(self, event: GenericEvent) -> None:
        pass
