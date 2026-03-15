from abc import ABC, abstractmethod

from discount_service.core.application.ports.patterns.unit_of_work.unit_of_work import AbstractUnitOfWork


class IUnitOfWorkFactory(ABC):
    @abstractmethod
    async def create(self) -> AbstractUnitOfWork:
        pass
