from __future__ import annotations

from typing import override

from dependency_injector import providers

from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.backend_patterns.unit_of_work.unit_of_work import AbstractUnitOfWork


class DjangoUnitOfWorkProvider(IUnitOfWorkProvider):
    def __init__(self, di_unit_of_work_provider: providers.Provider[AbstractUnitOfWork]) -> None:
        self.__di_unit_of_work_provider = di_unit_of_work_provider

    @override
    async def provide(self) -> AbstractUnitOfWork:
        return self.__di_unit_of_work_provider()
