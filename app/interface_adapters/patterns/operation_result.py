from dataclasses import dataclass, field
from typing import Any, Self

from app.main_error import MainError


@dataclass(frozen=True)
class ErrorViewModel:
    message: str
    error_code: str | None = field(default=None)
    details: dict[str, Any] | None = field(default=None)

    @classmethod
    def from_main_error(cls, exc: MainError) -> Self:
        return cls(message=exc.message, error_code=exc.error_code, details=exc.details)


@dataclass(frozen=True)
class Result[T]:
    success_value: T | None = field(default=None)
    error_value: ErrorViewModel | None = field(default=None)

    @property
    def is_succeed(self) -> bool:
        return self.success_value is not None and self.error_value is None
