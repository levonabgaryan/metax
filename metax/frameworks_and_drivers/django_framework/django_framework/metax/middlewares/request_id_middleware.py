import uuid
from collections.abc import Awaitable, Callable, Iterable

from asgiref.typing import ASGIReceiveEvent, ASGISendEvent, HTTPResponseStartEvent, WWWScope
from django_asgi_lifespan.handler import LifespanASGIHandler

from metax_logger.request_id_filter import request_id_scope

ASGIApp = Callable[
    [WWWScope, Callable[[], Awaitable[ASGIReceiveEvent]], Callable[[ASGISendEvent], Awaitable[None]]],
    Awaitable[None],
]


class ASGIRequestIDMiddleware:
    def __init__(self, app: ASGIApp | LifespanASGIHandler) -> None:
        self.app = app

    async def __call__(
        self,
        scope: WWWScope,
        receive: Callable[[], Awaitable[ASGIReceiveEvent]],
        send: Callable[[ASGISendEvent], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers_: Iterable[tuple[bytes, bytes]] = scope.get("headers", [])
        headers_dict = dict(headers_)

        incoming_bytes = headers_dict.get(b"x-request-id", b"")
        request_id = incoming_bytes.decode("utf-8").strip() or str(uuid.uuid7())

        async def put_request_id_in_response_headers(message: ASGISendEvent) -> None:
            if message["type"] == "http.response.start":
                response_event: HTTPResponseStartEvent = message
                response_headers = list(response_event.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode()))
                response_event["headers"] = response_headers
            await send(message)

        with request_id_scope(request_id):
            await self.app(scope, receive, put_request_id_in_response_headers)
