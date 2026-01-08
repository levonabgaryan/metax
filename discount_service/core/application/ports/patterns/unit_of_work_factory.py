from abc import ABC, abstractmethod

from discount_service.core.application.ports.patterns.unit_of_work import UnitOfWork


class IUnitOfWorkFactory(ABC):
    @abstractmethod
    def create(self) -> UnitOfWork:
        pass
