from abc import ABC, abstractmethod
from typing import TypeVar

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork


class RequestDTO:
    pass


class ResponseDTO:
    pass


class EmptyRequestDTO(RequestDTO):
    pass


class EmptyResponseDTO(ResponseDTO):
    pass


GenericRequestDTO = TypeVar("GenericRequestDTO", bound=RequestDTO)
GenericResponseDTO = TypeVar("GenericResponseDTO", bound=ResponseDTO)


class UseCase[GenericRequestDTO, GenericResponseDTO](ABC):
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    @abstractmethod
    async def execute(self, request: GenericRequestDTO) -> GenericResponseDTO:
        pass
