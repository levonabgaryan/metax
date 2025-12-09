from dataclasses import dataclass, field
from typing import Any, Self

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

    @classmethod
    def is_error_view_model(cls, obj: object) -> bool:
        return isinstance(obj, cls)
