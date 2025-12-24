from abc import ABC, abstractmethod
from typing import Any, Generic

from backend.core.application.patterns.use_case_abc import GenericResponseDTO, EmptyResponseDTO
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel
from backend.interface_adapters.patterns.operation_result import ErrorViewModel, GenericViewModel


class BasePresenter(ABC, Generic[GenericViewModel, GenericResponseDTO]):
    @staticmethod
    def present_empty(response: EmptyResponseDTO = EmptyResponseDTO()) -> EmptyViewModel:
        return EmptyViewModel()

    @staticmethod
    def present_error(message: str, error_code: str, details: dict[str, Any] | None = None) -> ErrorViewModel:
        return ErrorViewModel(message=message, error_code=error_code, details=details)

    @abstractmethod
    def present(self, response: GenericResponseDTO) -> GenericViewModel:
        pass
