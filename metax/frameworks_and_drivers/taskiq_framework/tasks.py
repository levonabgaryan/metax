from __future__ import annotations

import asyncio
import datetime as dt
import logging
import uuid

from metax.core.application.ddd_patterns.services.category_classifier_service import CategoryClassifierService
from metax.core.application.event_handlers.event_bus import EventBus
from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.application.use_cases.discounted_product.collect_discounted_products import (
    CollectDiscountedProducts,
)
from metax.core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsRequest
from metax.core.domain.entities.retailer.value_objects import RetailersNames, parse_retailer_name
from metax.frameworks_and_drivers.design_patterns.factories.discounted_product_collector_service_creators import (
    SasAmDiscountProductCollectorCreator,
    YerevanCityDiscountProductCollectorCreator,
)
from metax_bootstrap import METAX_LIFESPAN_MANAGER
from metax_logger.request_id_filter import request_id_scope

from .broker import broker_
from .errors import NoRetailersError

logger = logging.getLogger(__name__)


async def collect_discounted_products_from_all_retailers(
    unit_of_work_provider: IUnitOfWorkProvider,
    event_bus: EventBus,
    category_classifier_service: CategoryClassifierService,
    start_date_of_collecting: dt.datetime,
) -> None:
    uow = await unit_of_work_provider.provide()
    async with uow:
        retailers = [r async for r in uow.retailer_repo.all()]
    if not retailers:
        raise NoRetailersError

    tasks = []
    for retailer in retailers:
        retailer_key = retailer.get_name()
        collector_service_creator_class = RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP[
            parse_retailer_name(retailer_key)
        ]

        collector_service_creator: DiscountedProductCollectorServiceCreator
        if collector_service_creator_class is YerevanCityDiscountProductCollectorCreator:
            collector_service_creator = YerevanCityDiscountProductCollectorCreator(
                start_date_of_collecting=start_date_of_collecting,
                retailer=retailer,
            )
        elif collector_service_creator_class is SasAmDiscountProductCollectorCreator:
            collector_service_creator = SasAmDiscountProductCollectorCreator(
                start_date_of_collecting=start_date_of_collecting,
                retailer=retailer,
            )

        else:
            msg = f"Unsupported discounted product collector service creator: {collector_service_creator_class!r}"
            raise NotImplementedError(msg)

        use_case_request = CollectDiscountedProductsRequest(start_date_of_collecting=start_date_of_collecting)
        use_case = CollectDiscountedProducts(
            unit_of_work_provider=unit_of_work_provider,
            discounted_product_collector_service_creator=collector_service_creator,
            category_classifier_service=category_classifier_service,
            event_bus=event_bus,
        )
        tasks.append(use_case.handle_use_case(request=use_case_request))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Error during collection: {result}", exc_info=result)


async def _taskiq_collect_discounted_products_from_all_retailers(request_id: str | None = None) -> None:
    effective_id = request_id or f"gen-{uuid.uuid7()}"

    with request_id_scope(effective_id):
        metax_application_manager = METAX_LIFESPAN_MANAGER
        container = metax_application_manager.get_metax_container()
        unit_of_work_provider = container.get_unit_of_work_provider()
        category_classifier_service = container.get_category_classifier_service()
        event_bus = await container.get_event_bus()

        started_time = dt.datetime.now(tz=dt.UTC)

        await collect_discounted_products_from_all_retailers(
            unit_of_work_provider=unit_of_work_provider,
            category_classifier_service=category_classifier_service,
            start_date_of_collecting=started_time,
            event_bus=event_bus,
        )


@broker_.task(
    task_name="CollectDiscountedProducts",
    schedule=[
        {
            "cron": "0 21 * * *",  # 21:00 on UTC (01:00 in Armenia)
            "args": [None],
        }
    ],
)
async def taskiq_collect_discounted_products_from_all_retailers(request_id: str | None = None) -> None:
    await _taskiq_collect_discounted_products_from_all_retailers(request_id=request_id)


RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP: dict[
    RetailersNames, type[DiscountedProductCollectorServiceCreator]
] = {
    RetailersNames.YEREVAN_CITY: YerevanCityDiscountProductCollectorCreator,
    RetailersNames.SAS_AM: SasAmDiscountProductCollectorCreator,
}
