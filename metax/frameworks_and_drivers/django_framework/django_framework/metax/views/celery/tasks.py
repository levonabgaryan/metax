from datetime import UTC, datetime
from http import HTTPStatus
from typing import override

from django.http import HttpResponse
from dmr import Controller, ResponseSpec, modify
from dmr.endpoint import Endpoint
from dmr.errors import ErrorModel
from dmr.plugins.pydantic import PydanticSerializer

from metax.frameworks_and_drivers.celery_framework.errors import NoRetailersError
from metax.frameworks_and_drivers.celery_framework.tasks import collect_discounted_products_from_all_retailers
from metax_bootstrap import get_metax_lifespan_manager


class CollectDiscountedProductsFromRetailersController(Controller[PydanticSerializer]):
    @modify(
        tags=["Celery-tasks"],
        status_code=HTTPStatus.NO_CONTENT,
        extra_responses=[
            ResponseSpec(ErrorModel, status_code=HTTPStatus.SERVICE_UNAVAILABLE),
        ],
    )
    async def post(self) -> None:
        container = get_metax_lifespan_manager().get_di_container()
        patterns = container.patterns_container.container
        unit_of_work_provider = patterns.unit_of_work_provider()
        event_bus = await container.resources_container.container.event_bus.async_()
        category_classifier_service = patterns.category_classifier_service()
        now = datetime.now(tz=UTC)
        await collect_discounted_products_from_all_retailers(
            start_date_of_collecting=now,
            event_bus=event_bus,
            unit_of_work_provider=unit_of_work_provider,
            category_classifier_service=category_classifier_service,
        )

    @override
    async def handle_async_error(
        self, endpoint: Endpoint, controller: Controller[PydanticSerializer], exc: Exception
    ) -> HttpResponse:
        if isinstance(exc, NoRetailersError):
            raw_data = self.format_error(error=exc.error_code)
            return self.to_error(
                raw_data=raw_data,
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            )
        return await super().handle_async_error(endpoint, controller, exc)
