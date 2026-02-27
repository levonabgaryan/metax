import asyncio
from datetime import datetime, timezone

from .celery_application import celery_app
from dependency_injector.wiring import inject, Provide

from ..di import ServiceContainer
from ..di.scrappers_adapters_selector_container import (
    ScrappersAdaptersSelectorContainer,
    get_scrapper_adapter_name,
)
from ..patterns.services.discounted_products_collector_services import (
    DiscountedProductsCollectorServiceFromRetailer,
)
from ..scrappers_adapters.scrapper_adapter import ScrapperAdapter
from discount_service.core.application.patterns.services.category_classifier_service import (
    CategoryClassifierService,
)
from ...core.application.event_handlers.event_bus import EventBus
from ...core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from ...core.application.use_cases.discounted_product.collect_discounted_products import CollectDiscountedProducts
from ...core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsRequest


async def collect_discounted_products_from_all_retailers(
    unit_of_work: AbstractUnitOfWork,
    event_bus: EventBus,
    scrappers_adapters_selector_container: ScrappersAdaptersSelectorContainer,
    category_classifier_service: CategoryClassifierService,
    started_time: datetime,
) -> None:
    tasks = []
    all_retailers = unit_of_work.retailer_repo.get_all()
    async for retailer in all_retailers:
        adapter_key = get_scrapper_adapter_name(retailer_name=retailer.get_name())
        scrapper_adapter: ScrapperAdapter = scrappers_adapters_selector_container.scrapper_adapter(adapter_key)
        collector_service = DiscountedProductsCollectorServiceFromRetailer(
            retailer=retailer, scrapper_adapter=scrapper_adapter
        )
        use_case_request = CollectDiscountedProductsRequest(started_time=started_time)
        use_case = CollectDiscountedProducts(
            unit_of_work=unit_of_work,
            discounted_product_collector_service=collector_service,
            category_classifier_service=category_classifier_service,
            event_bus=event_bus,
        )
        tasks.append(use_case.handle_use_case(request=use_case_request))
    await asyncio.gather(*tasks)


@celery_app.task(name="CollectDiscountedProducts")
@inject
async def celery_task_collect_discounted_products_from_all_retailers(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    scrappers_adapters_selector_container: ScrappersAdaptersSelectorContainer = Provide[
        ServiceContainer.scrappers_adapters_selector_container
    ],
    category_classifier_service: CategoryClassifierService = Provide[
        ServiceContainer.patterns_container.container.category_classifier_service
    ],
    event_bus: EventBus = Provide[ServiceContainer.patterns_container.event_bus],
) -> None:
    started_time = datetime.now(tz=timezone.utc)

    await collect_discounted_products_from_all_retailers(
        unit_of_work=unit_of_work,
        scrappers_adapters_selector_container=scrappers_adapters_selector_container,
        category_classifier_service=category_classifier_service,
        started_time=started_time,
        event_bus=event_bus,
    )
