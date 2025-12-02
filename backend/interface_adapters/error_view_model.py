from dataclasses import dataclass, field
from typing import Any, Self

from backend.core.application.patterns.result_type import Error


@dataclass(frozen=True)
class ErrorViewModel:
    """
    Represents a client-facing version of a domain error.

    Use the `from_error` class-method to create an instance of this class from a domain Error.
    """

    message: str
    error_code: str | None = field(default=None)
    details: dict[str, Any] | None = field(default=None)

    @classmethod
    def from_error(cls, exc: Error) -> Self:
        return cls(message=exc.message, error_code=exc.error_code, details=exc.details)

    @classmethod
    def is_error_view_model(cls, obj: object) -> bool:
        return isinstance(obj, cls)
