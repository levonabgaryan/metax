from __future__ import annotations

from abc import ABC, abstractmethod

from metax.core.application.ports.backend_patterns.unit_of_work.unit_of_work import AbstractUnitOfWork


class IUnitOfWorkProvider(ABC):
    @abstractmethod
    async def provide(self) -> AbstractUnitOfWork:
        pass
