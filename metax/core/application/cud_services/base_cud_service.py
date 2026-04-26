from abc import ABC, abstractmethod

from metax.core.application.base_dtos.base_dtos import RequestDTO, ResponseDTO
from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider


class CUDService[GenericRequestDTO: RequestDTO](ABC):
    """Base class for create, update and delete actions for aggregate root entities."""

    def __init__(self, unit_of_work_provider: IUnitOfWorkProvider, event_bus: EventBus) -> None:
        self._unit_of_work_provider = unit_of_work_provider
        self._event_bus = event_bus

    @abstractmethod
    async def execute(self, request: GenericRequestDTO) -> ResponseDTO:
        pass
