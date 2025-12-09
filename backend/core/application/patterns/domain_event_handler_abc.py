from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic

from backend.core.application.patterns.unit_of_work import UnitOfWork
from backend.core.domain.domain_event import GenericDomainEvent


class DomainEventHandler(Generic[GenericDomainEvent], ABC):
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    @abstractmethod
    async def handle(self, domain_event: GenericDomainEvent) -> None:
        pass
