from pydantic import BaseModel
from http import HTTPStatus

from dmr import Controller, modify
from dmr.plugins.msgspec import MsgspecSerializer


class HealthCheckResponseBody(BaseModel):
    message: str = "Metax is working"


class HealthCheckView(Controller[MsgspecSerializer]):
    @modify(status_code=HTTPStatus.OK, tags=["Health"])
    async def get(self) -> HealthCheckResponseBody:
        return HealthCheckResponseBody()
