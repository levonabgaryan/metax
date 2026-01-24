from dependency_injector import providers

from discount_service.core.application.ports.patterns.unit_of_work_factory import IUnitOfWorkFactory
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork


class DjangoUnitOfWorkFactory(IUnitOfWorkFactory):
    def __init__(self, unit_of_work_provider: providers.Provider[AbstractUnitOfWork]) -> None:
        self.unit_of_work_provider = unit_of_work_provider

    def create(self) -> AbstractUnitOfWork:
        return self.unit_of_work_provider()
