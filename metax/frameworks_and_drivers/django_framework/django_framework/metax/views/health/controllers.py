from http import HTTPStatus

from dmr import modify
from pydantic import BaseModel

from django_framework.metax.views.json_api_controller import MetaxJsonApiController


class HealthCheckResponseBody(BaseModel):
    message: str = "Metax is working"


class HealthCheckView(MetaxJsonApiController):
    @modify(status_code=HTTPStatus.OK, tags=["Health"], auth=None)
    async def get(self) -> HealthCheckResponseBody:
        return HealthCheckResponseBody()
