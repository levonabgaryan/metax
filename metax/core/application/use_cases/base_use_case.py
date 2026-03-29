from abc import abstractmethod, ABC

from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.patterns.providers.unit_of_work_provider import IUnitOfWorkProvider


class RequestDTO:
    pass


class ResponseDTO:
    pass


class UseCase[GenericRequestDTO: RequestDTO](ABC):
    def __init__(self, unit_of_work_provider: IUnitOfWorkProvider, event_bus: EventBus) -> None:
        self._unit_of_work_provider = unit_of_work_provider
        self._event_bus = event_bus

    @abstractmethod
    async def handle_use_case(self, request: GenericRequestDTO) -> ResponseDTO:
        pass
