from http import HTTPStatus

from dmr import Controller, modify
from dmr.plugins.pydantic import PydanticSerializer
from pydantic import BaseModel


class HealthCheckResponseBody(BaseModel):
    message: str = "Metax is working"


class HealthCheckView(Controller[PydanticSerializer]):
    @modify(status_code=HTTPStatus.OK, tags=["Health"])
    async def get(self) -> HealthCheckResponseBody:
        return HealthCheckResponseBody()
