from dataclasses import dataclass, field
from typing import Any, Self

from backend.core.domain.domain_error import DomainError


@dataclass(frozen=True)
class Error:
    """Standardized Domain error information"""

    message: str
    error_code: str | None = field(default=None)
    details: dict[str, Any] | None = field(default=None)

    @classmethod
    def from_domain_error(cls, exc: DomainError) -> Self:
        return cls(message=exc.message, error_code=exc.error_code, details=exc.details)


@dataclass(frozen=True)
class Result[T]:
    _success_value: T | None = None
    _error_value: Error | None = None

    @property
    def is_succeed(self) -> bool:
        return self._success_value is not None and self._error_value is None

    @classmethod
    def from_success(cls, value: T) -> Self:
        """
        Creates a Result instance representing a successful outcome.

        Always use this method to create a successful result.
        """
        return cls(_success_value=value)

    @classmethod
    def from_error(cls, value: Error) -> Self:
        """
        Creates a Result instance representing an error.

        Always use this method to create a result containing an error.
        """
        return cls(_error_value=value)

    def get_success_value(self) -> T:
        """
        Returns the success value if present.

        This getter exists primarily for static type checkers (e.g., mypy), ensuring
        the value is not None when accessed. Raises AttributeError if no success value is set.
        """
        if self._success_value is None:
            msg = f"Instance of {type(self).__name__} has no attribute 'success_value'"
            raise AttributeError(msg)
        return self._success_value

    def get_error_value(self) -> Error:
        """
        Returns the error object if present.

        This getter exists primarily for static type checkers (e.g., mypy), ensuring
        the value is not None when accessed. Raises AttributeError if no error is set.
        """
        if self._error_value is None:
            msg = f"Instance of {type(self).__name__} has no attribute 'error_value'"
            raise AttributeError(msg)
        return self._error_value
