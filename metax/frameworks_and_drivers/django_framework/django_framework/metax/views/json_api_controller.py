from copy import deepcopy
from http import HTTPStatus
from typing import ClassVar, TypedDict, override
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.http import HttpResponse
from django_framework.metax.views.json_parsers import JsonApiParser, JsonApiRenderer
from dmr import Controller
from dmr.endpoint import Endpoint
from dmr.errors import ErrorType
from dmr.exceptions import ValidationError
from dmr.plugins.pydantic import PydanticSerializer
from pydanja import DANJAError, DANJALink, DANJASource

from metax.core.application.ports.ddd_patterns.repository.errors import (
    EntityAlreadyExistsError,
    EntityIsNotFoundError,
)
from metax_main_error import MetaxError


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
    parsers: ClassVar[list[JsonApiParser]] = [JsonApiParser()]
    renderers: ClassVar[list[JsonApiRenderer]] = [JsonApiRenderer()]

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

    @override
    async def handle_async_error(
        self,
        endpoint: Endpoint,
        controller: Controller[PydanticSerializer],
        exc: Exception,
    ) -> HttpResponse:
        if isinstance(exc, EntityIsNotFoundError):
            return self.to_error(
                raw_data=DANJAError(code=exc.error_code, title=exc.title, detail=exc.details),
                status_code=HTTPStatus.NOT_FOUND,
            )
        if isinstance(exc, EntityAlreadyExistsError):
            return self.to_error(
                raw_data=DANJAError(code=exc.error_code, title=exc.title, detail=exc.details),
                status_code=HTTPStatus.CONFLICT,
            )
        if isinstance(exc, MetaxError):
            return self.to_error(
                raw_data=DANJAError(code=exc.error_code, title=exc.title, detail=exc.details),
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        return await super().handle_async_error(endpoint, controller, exc)

    def _build_pagination_links(
        self, current_url: str, offset: int, limit: int, total_count: int
    ) -> dict[str, str | DANJALink | None]:
        prev_offset = (
            None if offset == 0 else max(0, offset - limit)
        )  # we could use just offset - limit, but max is for safety
        next_offset = None if offset + limit >= total_count else offset + limit

        last_item_idx = total_count - 1
        first_index_of_last_block = last_item_idx // limit
        last_offset = 0 if total_count == 0 else first_index_of_last_block * limit

        links: dict[str, str | DANJALink | None] = {
            "self": current_url,
            "first": self.__make_new_url_by_limit_and_offset(current_url, offset=0, limit=limit),
            "last": self.__make_new_url_by_limit_and_offset(current_url, offset=last_offset, limit=limit),
        }
        if prev_offset is None:
            links["prev"] = None
        else:
            links["prev"] = self.__make_new_url_by_limit_and_offset(current_url, offset=prev_offset, limit=limit)

        if next_offset is None:
            links["next"] = None
        else:
            links["next"] = self.__make_new_url_by_limit_and_offset(current_url, offset=next_offset, limit=limit)

        return links

    @staticmethod
    def __make_new_url_by_limit_and_offset(url_: str, limit: int, offset: int) -> str:
        parsed_url = urlparse(url_)
        query_params = {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
        new_query_params = deepcopy(query_params)
        new_query_params["page[limit]"] = str(limit)
        new_query_params["page[offset]"] = str(offset)

        new_query = urlencode(new_query_params)
        return urlunparse((
            str(parsed_url.scheme),
            str(parsed_url.netloc),
            str(parsed_url.path),
            str(parsed_url.params),
            new_query,
            str(parsed_url.fragment),
        ))


# discounted product API
# asyncio, Open-search, subprocess(sync and async)
# best practise for docker containers (testing, local launch, for deployment)
# django admin
