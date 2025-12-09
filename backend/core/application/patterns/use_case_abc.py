from abc import ABC, abstractmethod
from typing import TypeVar


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
    @abstractmethod
    async def execute(self, request: GenericRequestDTO) -> GenericResponseDTO:
        pass
