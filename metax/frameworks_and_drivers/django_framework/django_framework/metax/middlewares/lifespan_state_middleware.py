r"""ASGI lifespan state on ``request.state`` — tolerant when ``scope["state"]`` is absent.

``django.test.AsyncClient`` does not run the lifespan protocol, so ``LifespanStateMiddleware``
from django-asgi-lifespan raises ``KeyError`` without this fallback (see tests using ``DMRAsyncClient``).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.core.handlers.asgi import ASGIRequest
from django.http import HttpRequest, HttpResponseBase


class SafeLifespanStateMiddleware:
    async_capable = True
    sync_capable = False

    def __init__(
        self,
        get_response: Callable[[HttpRequest], Awaitable[HttpResponseBase]],
    ) -> None:
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    async def __call__(self, request: HttpRequest) -> HttpResponseBase:
        if isinstance(request, ASGIRequest):
            request.state = request.scope.get("state", {})
        else:
            request.state = {}
        return await self.get_response(request)
