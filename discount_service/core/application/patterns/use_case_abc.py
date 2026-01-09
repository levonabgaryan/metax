from abc import ABC, abstractmethod
from typing import TypeVar

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork


class RequestDTO:
    pass


class ResponseDTO:
    pass


GenericRequestDTO = TypeVar("GenericRequestDTO", bound=RequestDTO)
GenericResponseDTO = TypeVar("GenericResponseDTO", bound=ResponseDTO)


class UseCase[GenericRequestDTO, GenericResponseDTO](ABC):
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    @abstractmethod
    async def execute(self, request: GenericRequestDTO) -> GenericResponseDTO:
        pass
