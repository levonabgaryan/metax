from datetime import UTC, datetime
from http import HTTPStatus

from django_framework.metax.views.json_api_controller import MetaxJsonApiController
from dmr import ResponseSpec, modify
from dmr.errors import ErrorModel

from metax.frameworks_and_drivers.celery_framework.tasks import collect_discounted_products_from_all_retailers
from metax_bootstrap import get_metax_lifespan_manager


class CollectDiscountedProductsFromRetailersController(MetaxJsonApiController):
    @modify(
        tags=["Celery-tasks"],
        status_code=HTTPStatus.NO_CONTENT,
        extra_responses=[
            ResponseSpec(ErrorModel, status_code=HTTPStatus.SERVICE_UNAVAILABLE),
        ],
    )
    async def post(self) -> None:
        container = get_metax_lifespan_manager().get_metax_container()
        unit_of_work_provider = container.get_unit_of_work_provider()
        event_bus = await container.get_event_bus()
        category_classifier_service = container.get_category_classifier_service()
        now = datetime.now(tz=UTC)
        await collect_discounted_products_from_all_retailers(
            start_date_of_collecting=now,
            event_bus=event_bus,
            unit_of_work_provider=unit_of_work_provider,
            category_classifier_service=category_classifier_service,
        )
