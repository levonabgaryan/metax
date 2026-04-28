from http import HTTPStatus

from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from dmr import modify
from pydantic import BaseModel


class HealthCheckResponseBody(BaseModel):
    message: str = "Metax is working"


class HealthCheckView(MetaxJsonApiController):
    @modify(status_code=HTTPStatus.OK, tags=["Health"])
    async def get(self) -> HealthCheckResponseBody:
        return HealthCheckResponseBody()
