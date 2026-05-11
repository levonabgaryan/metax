from typing import Self, override

from dmr.controller import Controller
from dmr.endpoint import Endpoint
from dmr.exceptions import NotAuthenticatedError
from dmr.security.jwt import JWTAsyncAuth
from dmr.serializer import BaseSerializer


class AdminJWTAsyncAuth(JWTAsyncAuth):
    @override
    async def __call__(self, endpoint: Endpoint, controller: Controller[BaseSerializer]) -> Self | None:
        result = await super().__call__(endpoint, controller)
        if result is None:
            return None
        if not controller.request.user.is_staff:
            msg = "Admin access required"
            raise NotAuthenticatedError(msg=msg)
        return result
