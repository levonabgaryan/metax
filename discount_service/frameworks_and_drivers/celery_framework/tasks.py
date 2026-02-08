import asyncio
from datetime import datetime, timezone

from dependency_injector.wiring import inject, Provide

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.use_cases.discounted_product.collect_discounted_products_from_retailer import (
    CollectDiscountedProductsFromRetailer,
)
from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsFromRetailerRequest,
)
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from .celery_application import celery_app


@celery_app.task(name="CollectDiscountedProductsFromRetailer")
async def celery_task_collect_discounted_products_from_all_retailers() -> None:
    await collect_discounted_products_from_all_retailers()


@inject
async def collect_discounted_products_from_all_retailers(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    use_case: CollectDiscountedProductsFromRetailer = Provide[
        ServiceContainer.use_cases_container.container.discounted_product.container.collect_discounted_products_from_retailer
    ],
) -> None:
    current_time = datetime.now(timezone.utc)
    retailer_repo = unit_of_work.retailer_repo
    retailers_urls = await retailer_repo.get_all_retailers_urls()
    tasks = []
    for retailer_url in retailers_urls:
        use_case_request = CollectDiscountedProductsFromRetailerRequest(
            retailer_url=retailer_url,
            started_time=current_time,
        )
        tasks.append(use_case.execute(request=use_case_request))

    await asyncio.gather(*tasks)
