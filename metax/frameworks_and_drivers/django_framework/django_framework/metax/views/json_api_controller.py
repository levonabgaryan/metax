from http import HTTPStatus
from typing import ClassVar, TypedDict, override

from dmr import Controller
from dmr.errors import ErrorType
from dmr.exceptions import ValidationError
from dmr.plugins.pydantic import PydanticSerializer
from pydanja import DANJAError, DANJASource


def _to_json_api_pointer(loc: list[int | str] | None) -> str | None:
    if not loc:
        return None

    parts: list[str] = []
    for chunk in loc:
        if chunk in ("parsed_body", "parsed_path", "parsed_query", "parsed_headers"):
            continue
        parts.append(str(chunk))

    if not parts:
        return None

    return "/" + "/".join(parts)


class JsonApiErrorModel(TypedDict):
    errors: list[DANJAError]


class MetaxJsonApiController(Controller[PydanticSerializer]):
    error_model: ClassVar[type[JsonApiErrorModel]] = JsonApiErrorModel

    @override
    def format_error(
        self,
        error: str | Exception,
        *,
        loc: str | list[str | int] | None = None,
        error_type: str | ErrorType | None = None,
    ) -> JsonApiErrorModel:
        if isinstance(error, ValidationError):
            items = []
            for item in error.payload:
                pointer = _to_json_api_pointer(item.get("loc"))
                items.append(
                    DANJAError(
                        code=item.get("type"),
                        title="Validation Error",
                        detail=item["msg"],
                        source=DANJASource(pointer=pointer) if pointer else None,
                        status=str(error.status_code.value),
                    )
                )
            return {"errors": items}

        msg = str(error)
        code = str(error_type or "internal_error")
        return {
            "errors": [
                DANJAError(
                    code=code,
                    title="Error",
                    detail=msg,
                    status=str(HTTPStatus.INTERNAL_SERVER_ERROR.value),
                )
            ]
        }
