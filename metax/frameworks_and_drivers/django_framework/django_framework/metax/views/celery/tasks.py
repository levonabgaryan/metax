from datetime import datetime, timezone
from http import HTTPStatus
from typing import override

from django.http import HttpResponse
from dmr import Controller, modify, ResponseSpec
from dmr.endpoint import Endpoint
from dmr.errors import ErrorModel
from dmr.plugins.msgspec import MsgspecSerializer

from metax.frameworks_and_drivers.celery_framework.errors import NoRetailersError
from metax.frameworks_and_drivers.celery_framework.tasks import collect_discounted_products_from_all_retailers
from metax.frameworks_and_drivers.di.metax_container import get_metax_container


class CollectDiscountedProductsFromRetailersController(Controller[MsgspecSerializer]):
    @modify(
        tags=["Celery-tasks"],
        status_code=HTTPStatus.NO_CONTENT,
        extra_responses=[
            ResponseSpec(ErrorModel, status_code=HTTPStatus.SERVICE_UNAVAILABLE),
        ],
    )
    async def post(self) -> None:
        container = get_metax_container()
        unit_of_work = await container.patterns_container.container.unit_of_work.async_()
        event_bus = container.patterns_container.container.event_bus()
        category_classifier_service = (
            await container.patterns_container.container.category_classifier_service.async_()
        )
        now = datetime.now(tz=timezone.utc)
        await collect_discounted_products_from_all_retailers(
            start_date_of_collecting=now,
            event_bus=event_bus,
            unit_of_work=unit_of_work,
            category_classifier_service=category_classifier_service,
        )

    @override
    async def handle_async_error(
        self, endpoint: Endpoint, controller: Controller[MsgspecSerializer], exc: Exception
    ) -> HttpResponse:
        if isinstance(exc, NoRetailersError):
            raw_data = self.format_error(error=exc.error_code)
            return self.to_error(
                raw_data=raw_data,
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            )
        return await super().handle_async_error(endpoint, controller, exc)
