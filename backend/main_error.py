from typing import Any, Optional


class MainError(Exception):
    def __init__(
        self,
        message: str = "An error occurred",
        error_code: str | None = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message
        )  # https://peps.python.org/pep-0352/#:~:text=No%20restriction%20is,in%20a%20subclass.
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.exc_type = self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.exc_type}(message={self.message}, error_code={self.error_code}, details={self.details})"  # noqa: E501
