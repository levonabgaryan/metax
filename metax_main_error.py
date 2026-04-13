from typing import Optional, override


class MetaxError(Exception):
    def __init__(
        self,
        *,
        error_code: str,
        title: str = "An error occurred",
        details: Optional[str] = None,
    ) -> None:
        super().__init__(
            title
        )  # https://peps.python.org/pep-0352/#:~:text=No%20restriction%20is,in%20a%20subclass.
        self.title = super().args[0]
        self.error_code = error_code
        self.details = details or "No details provided."

    @override
    def __repr__(self) -> str:
        return f"(title={self.title}, error_code={self.error_code}, details={self.details})"
