from typing import override

from constants import ErrorCodes


class MetaxError(Exception):
    """Base Exception class for all Metax Errors.

    :param str error_code: Error code
    :param str title: Short description of the error
    :param str details: Long description of the error
    """

    def __init__(
        self,
        *,
        title: str = "An error occurred",
        details: str | None = None,
        error_code: str = ErrorCodes.METAX_ERROR,
    ) -> None:
        super().__init__(
            details if details is not None else title
        )  # https://peps.python.org/pep-0352/#:~:text=No%20restriction%20is,in%20a%20subclass.

        self.title = title
        self.error_code = error_code
        self.details = details or "No details provided."

    @override
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"title={self.title!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r})"
        )

    @override
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.title} {self.details if self.details else ''}"
