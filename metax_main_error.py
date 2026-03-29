from typing import Any, Optional, override


class MetaxError(Exception):
    def __init__(
        self,
        *,
        error_code: str,
        message: str = "An error occurred",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message
        )  # https://peps.python.org/pep-0352/#:~:text=No%20restriction%20is,in%20a%20subclass.
        self.message = super().args[0]
        self.error_code = error_code
        self.details = details or {}
        self.exc_type = self.__class__.__name__

    @override
    def __repr__(self) -> str:
        return f"{self.exc_type}(message={self.message}, error_code={self.error_code}, details={self.details})"  # noqa: E501
