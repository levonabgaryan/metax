"""ASGI config for django_framework project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

from collections.abc import Awaitable, Callable

from asgiref.typing import ASGIReceiveEvent, ASGISendEvent, LifespanScope, WWWScope
from django_asgi_lifespan.asgi import get_asgi_application

from django_framework.metax.middlewares.request_id_middleware import ASGIRequestIDMiddleware

ASGIScope = WWWScope | LifespanScope
Receive = Callable[[], Awaitable[ASGIReceiveEvent]]
Send = Callable[[ASGISendEvent], Awaitable[None]]

django_application = get_asgi_application()
wrapped_application = ASGIRequestIDMiddleware(django_application)


async def application(scope: ASGIScope, receive: Receive, send: Send) -> None:
    if scope["type"] == "http":
        await wrapped_application(scope, receive, send)
        return
    if scope["type"] == "lifespan":
        await django_application(scope, receive, send)
        return
    msg = f"Unknown scope type {scope['type']}"
    raise NotImplementedError(msg)
