"""Fast-path middleware for ``/api/health``.

Bypasses the full Django middleware chain (security, sessions, CSRF, auth,
clickjacking, etc.) for the health endpoint. This makes the probe trivially
cheap and avoids contention with the rest of the request pipeline.

IMPORTANT: must be placed **first** in ``MIDDLEWARE`` to actually short-circuit
the chain.

Must also declare ``async_capable`` and call ``markcoroutinefunction`` so that
Django's ASGI handler treats this middleware as async (the ``__call__`` is
``async def``). Otherwise Django wraps it as sync and the un-awaited coroutine
leaks up the chain, crashing ``XFrameOptionsMiddleware.process_response`` with
``AttributeError: 'coroutine' object has no attribute 'get'``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponse, HttpResponseBase


class HealthCheckMiddleware:
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
        if request.path == "/api/health":
            return HttpResponse("ok", content_type="text/plain")
        return await self.get_response(request)
