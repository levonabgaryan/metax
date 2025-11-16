from dataclasses import dataclass, field, InitVar
from typing import Any, Self

from app.main_exception import MainException


@dataclass(frozen=True)
class Error:
    message: str
    error_code: str | None = field(default=None)
    details: dict[str, Any] | None = field(default=None)

    @classmethod
    def from_main_exception(cls, exc: MainException) -> Self:
        return cls(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details
        )


@dataclass(frozen=True)
class Result[T]:
    success_value: T | None = field(default=None)
    error_value: Error | None = field(default=None)

    @property
    def is_succeed(self) -> bool:
        return (
            self.success_value is not None
            and self.error_value is None
        )
