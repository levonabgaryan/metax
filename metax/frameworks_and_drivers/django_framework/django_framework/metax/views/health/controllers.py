import msgspec
from http import HTTPStatus

from dmr import Controller, modify
from dmr.plugins.msgspec import MsgspecSerializer


class HealthCheckResponseBody(msgspec.Struct):
    message: str = "Metax is working"


class HealthCheckView(Controller[MsgspecSerializer]):
    @modify(status_code=HTTPStatus.OK)
    async def get(self) -> HealthCheckResponseBody:
        return HealthCheckResponseBody()
