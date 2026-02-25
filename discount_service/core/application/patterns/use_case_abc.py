from abc import abstractmethod
from typing import TypeVar

from discount_service.core.application.patterns.mediator import BaseHandler


class RequestDTO:
    pass


class ResponseDTO:
    pass


GenericRequestDTO = TypeVar("GenericRequestDTO", bound=RequestDTO)
GenericResponseDTO = TypeVar("GenericResponseDTO", bound=ResponseDTO)


class UseCase[GenericRequestDTO, GenericResponseDTO](BaseHandler):
    @abstractmethod
    async def handle_use_case(self, request: GenericRequestDTO) -> GenericResponseDTO:
        pass
