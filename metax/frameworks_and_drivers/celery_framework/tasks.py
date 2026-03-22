from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from dependency_injector.wiring import Provide, inject

from config_ import metax_configs
from metax.core.application.patterns.services.category_classifier_service import CategoryClassifierService
from metax.core.application.patterns.strategies.discounted_product.discounted_product_collector_context import (
    DiscountedProductCollectorContext,
)
from metax.core.application.patterns.strategies.discounted_product.discounted_product_collector_strategy import (
    DiscountedProductCollectorStrategy,
)
from metax.core.application.ports.patterns.unit_of_work.unit_of_work import AbstractUnitOfWork
from metax.core.application.use_cases.discounted_product.collect_discounted_products import (
    CollectDiscountedProducts,
)
from metax.core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsRequest
from metax.core.application.event_handlers.event_bus import EventBus
from metax.frameworks_and_drivers.patterns.strategies.discounted_product.sas_am_strategy import SasAmStrategy
from metax.frameworks_and_drivers.patterns.strategies.discounted_product.yerevan_city_strategy import (
    YerevanCityStrategy,
)

from ..di import ServiceContainer
from .celery_application import celery_app
from ...core.domain.entities.retailer.value_objects import RetailersNames


async def collect_discounted_products_from_all_retailers(
    unit_of_work: AbstractUnitOfWork,
    event_bus: EventBus,
    category_classifier_service: CategoryClassifierService,
    start_date_of_collecting: datetime,
) -> None:
    tasks = []
    all_retailers = unit_of_work.retailer_repo.get_all()
    async for retailer in all_retailers:
        retailer_key = retailer.get_name()
        strategy_class = RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_STRATEGY[retailer_key]

        strategy: DiscountedProductCollectorStrategy
        if strategy_class is YerevanCityStrategy:
            strategy = YerevanCityStrategy(
                yerevan_city_data_source_url=metax_configs.yerevan_city_data_source_url,
                yerevan_city_products_details_url=metax_configs.yerevan_city_products_details_url,
                retailer=retailer,
            )
        elif strategy_class is SasAmStrategy:
            strategy = SasAmStrategy(
                sas_am_data_source_url=metax_configs.sas_am_data_source_url,
                sas_am_main_page_url=metax_configs.sas_am_main_page_url,
                retailer=retailer,
            )
        else:
            msg = f"Unsupported discounted product collector strategy: {strategy_class!r}"
            raise NotImplementedError(msg)

        discounted_product_collector_context = DiscountedProductCollectorContext(
            start_date_of_collecting=start_date_of_collecting,
            strategy=strategy,
        )
        use_case_request = CollectDiscountedProductsRequest(start_date_of_collecting=start_date_of_collecting)
        use_case = CollectDiscountedProducts(
            unit_of_work=unit_of_work,
            discounted_product_collector_context=discounted_product_collector_context,
            category_classifier_service=category_classifier_service,
            event_bus=event_bus,
        )
        tasks.append(use_case.handle_use_case(request=use_case_request))
    await asyncio.gather(*tasks)


@celery_app.task(name="CollectDiscountedProducts")
@inject
async def celery_task_collect_discounted_products_from_all_retailers(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    category_classifier_service: CategoryClassifierService = Provide[
        ServiceContainer.patterns_container.container.category_classifier_service
    ],
    event_bus: EventBus = Provide[ServiceContainer.patterns_container.event_bus],
) -> None:
    started_time = datetime.now(tz=timezone.utc)

    await collect_discounted_products_from_all_retailers(
        unit_of_work=unit_of_work,
        category_classifier_service=category_classifier_service,
        start_date_of_collecting=started_time,
        event_bus=event_bus,
    )


RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_STRATEGY: dict[
    RetailersNames, type[DiscountedProductCollectorStrategy]
] = {
    RetailersNames.YEREVAN_CITY: YerevanCityStrategy,
    RetailersNames.SAS_AM: SasAmStrategy,
}
