from dataclasses import dataclass, field
from typing import Any, Self, TypeVar

from backend.main_error import MainError


@dataclass(frozen=True)
class ErrorViewModel:
    """
    Represents a client-facing version of a `MaineError` class.

    Use the `from_error` class-method to create an instance of this class from a MainError.
    """

    message: str
    error_code: str | None = field(default=None)
    details: dict[str, Any] | None = field(default=None)

    @classmethod
    def from_error(cls, error: MainError) -> Self:
        return cls(message=error.message, error_code=error.error_code, details=error.details)


SuccessViewModel = TypeVar("SuccessViewModel")


@dataclass(frozen=True)
class OperationResult[SuccessViewModel]:
    _succeeded_view_model: SuccessViewModel | None = field(default=None)
    _error_view_model: ErrorViewModel | None = field(default=None)

    @property
    def is_succeeded(self) -> bool:
        return self._succeeded_view_model is not None and self._error_view_model is None

    def get_succeeded_view_model(self) -> SuccessViewModel:
        if self._succeeded_view_model is None:
            raise AttributeError(f"Instance of {type(self).__name__} has no attribute 'succeeded_view_model'")
        return self._succeeded_view_model

    def get_error_view_model(self) -> ErrorViewModel:
        if self._error_view_model is None:
            raise AttributeError(f"Instance of {type(self).__name__} has no attribute 'error_view_model'")
        return self._error_view_model

    @classmethod
    def from_error_view_model(cls, error_view_model: ErrorViewModel) -> Self:
        return cls(_error_view_model=error_view_model)

    @classmethod
    def from_succeeded_view_model(cls, succeeded_view_model: SuccessViewModel) -> Self:
        return cls(_succeeded_view_model=succeeded_view_model)
