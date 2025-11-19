from typing import Any, Optional


class MainError(Exception):
    def __init__(
        self,
        message: str = "An error occurred",
        error_code: str | None = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.exc_type = self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.exc_type}(message={self.message}, error_code={self.error_code}, details={self.details})"  # noqa: E501

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}" + (
            f" | Details: {self.details}" if self.details else ""
        )
