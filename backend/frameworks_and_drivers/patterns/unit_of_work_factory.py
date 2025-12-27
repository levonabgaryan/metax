from dependency_injector import providers

from backend.core.application.ports.patterns.unit_of_work_factory import IUnitOfWorkFactory
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork


class DjangoUnitOfWorkFactory(IUnitOfWorkFactory):
    def __init__(self, unit_of_work_provider: providers.Provider[UnitOfWork]) -> None:
        self.unit_of_work_provider = unit_of_work_provider

    def create(self) -> UnitOfWork:
        return self.unit_of_work_provider()
