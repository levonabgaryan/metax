from abc import ABC, abstractmethod
from typing import Any, Generic

from backend.core.application.patterns.use_case_abc import GenericResponseDTO
from backend.interface_adapters.patterns.operation_result import ErrorViewModel, GenericViewModel


class BasePresenter(ABC, Generic[GenericResponseDTO, GenericViewModel]):
    @staticmethod
    def present_error(message: str, error_code: str, details: dict[str, Any] | None = None) -> ErrorViewModel:
        return ErrorViewModel(message=message, error_code=error_code, details=details)

    @abstractmethod
    def present(self, response: GenericResponseDTO | None = None) -> GenericViewModel:
        pass
