import msgspec
from dmr import Controller
from dmr.plugins.msgspec import MsgspecSerializer
from dmr.routing import Router, path


class HealthCheckResponseBody(msgspec.Struct):
    message: str = "Metax is working"


class HealthCheckView(Controller[MsgspecSerializer]):
    async def get(self) -> HealthCheckResponseBody:
        return HealthCheckResponseBody()


router = Router(
    "health/",
    [
        path(
            route="check/",
            view=HealthCheckView.as_view(),
        )
    ],
)
