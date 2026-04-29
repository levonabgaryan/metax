from __future__ import annotations

import asyncio
from datetime import UTC, datetime

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
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.frameworks_and_drivers.design_patterns.factories.discounted_product_collector_service_creators import (
    SasAmDiscountProductCollectorCreator,
    YerevanCityDiscountProductCollectorCreator,
)
from metax_bootstrap import METAX_CONFIGS, get_metax_lifespan_manager

from .celery_application import celery_app
from .errors import NoRetailersError


async def collect_discounted_products_from_all_retailers(
    unit_of_work_provider: IUnitOfWorkProvider,
    event_bus: EventBus,
    category_classifier_service: CategoryClassifierService,
    start_date_of_collecting: datetime,
) -> None:
    metax_configs = METAX_CONFIGS
    uow = await unit_of_work_provider.provide()
    async with uow:
        retailers = [r async for r in uow.retailer_repo.all()]
    if not retailers:
        raise NoRetailersError

    tasks = []
    for retailer in retailers:
        retailer_key = retailer.get_name()
        collector_service_creator_class = RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP[
            RetailersNames(retailer_key)
        ]

        collector_service_creator: DiscountedProductCollectorServiceCreator
        if collector_service_creator_class is YerevanCityDiscountProductCollectorCreator:
            collector_service_creator = YerevanCityDiscountProductCollectorCreator(
                start_date_of_collecting=start_date_of_collecting,
                yerevan_city_products_details_url=metax_configs.yerevan_city_products_details_url,
                yerevan_city_data_source_url=metax_configs.yerevan_city_data_source_url,
                retailer=retailer,
            )
        elif collector_service_creator_class is SasAmDiscountProductCollectorCreator:
            collector_service_creator = SasAmDiscountProductCollectorCreator(
                start_date_of_collecting=start_date_of_collecting,
                retailer=retailer,
                sas_am_main_page_url=metax_configs.sas_am_main_page_url,
                sas_am_data_source_url=metax_configs.sas_am_data_source_url,
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
    await asyncio.gather(*tasks, return_exceptions=True)


@celery_app.task(name="CollectDiscountedProducts")
def celery_task_collect_discounted_products_from_all_retailers() -> None:
    asyncio.run(_celery_task_collect_discounted_products_from_all_retailers())


async def _celery_task_collect_discounted_products_from_all_retailers() -> None:
    metax_application_manager = get_metax_lifespan_manager()
    di_container = metax_application_manager.get_di_container()
    patterns = di_container.patterns_container.container
    unit_of_work_provider = patterns.unit_of_work_provider()
    category_classifier_service = patterns.category_classifier_service()
    event_bus = await di_container.resources_container.container.event_bus.async_()

    started_time = datetime.now(tz=UTC)

    await collect_discounted_products_from_all_retailers(
        unit_of_work_provider=unit_of_work_provider,
        category_classifier_service=category_classifier_service,
        start_date_of_collecting=started_time,
        event_bus=event_bus,
    )


RETAILER_NAME_DISCOUNTED_PRODUCT_COLLECTOR_SERVICE_CREATOR_MAP: dict[
    RetailersNames, type[DiscountedProductCollectorServiceCreator]
] = {
    RetailersNames.YEREVAN_CITY: YerevanCityDiscountProductCollectorCreator,
    RetailersNames.SAS_AM: SasAmDiscountProductCollectorCreator,
}
