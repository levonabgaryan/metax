"""ASGI config for django_framework project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

from typing import Awaitable, Callable

from asgiref.typing import ASGIReceiveEvent, ASGISendEvent, LifespanScope, WWWScope
from django_asgi_lifespan.asgi import get_asgi_application

ASGIScope = WWWScope | LifespanScope
Receive = Callable[[], Awaitable[ASGIReceiveEvent]]
Send = Callable[[ASGISendEvent], Awaitable[None]]

django_application = get_asgi_application()


async def application(scope: ASGIScope, receive: Receive, send: Send) -> None:
    if scope["type"] in {"http", "lifespan"}:
        await django_application(scope, receive, send)
    else:
        msg = f"Unknown scope type {scope['type']}"
        raise NotImplementedError(msg)
