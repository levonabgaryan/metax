from abc import ABC, abstractmethod

from backend.core.application.input_ports.patterns.unit_of_work import UnitOfWork


class IUnitOfWorkFactory(ABC):
    @abstractmethod
    def create(self) -> UnitOfWork:
        pass
