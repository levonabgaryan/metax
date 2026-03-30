from typing import Any, Optional, override


class MetaxError(Exception):
    def __init__(
        self,
        *,
        error_code: str,
        title: str = "An error occurred",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            title
        )  # https://peps.python.org/pep-0352/#:~:text=No%20restriction%20is,in%20a%20subclass.
        self.title = super().args[0]
        self.error_code = error_code
        self.details = details or {}

    @override
    def __repr__(self) -> str:
        return f"(title={self.title}, error_code={self.error_code}, details={self.details})"  # noqa: E501


# type -> URN urn:metax:<error-code>  # types is a string in JSON -> https://www.rfc-editor.org/rfc/rfc9457.html#name-type
# title -> A little bit about error  # title is a string in JSON -> https://www.rfc-editor.org/rfc/rfc9457.html#name-title
# status -> http status code  # status is a JSON number -> https://www.rfc-editor.org/rfc/rfc9457.html#name-status
# detail -> Explain error detailly  # detail is a JSON string https://www.rfc-editor.org/rfc/rfc9457.html#name-detail
# instance -> JSON string which is instance of type, I will use full endpoint path + domain + http -> https://www.rfc-editor.org/rfc/rfc9457.html#name-instance
