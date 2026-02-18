import asyncio
from datetime import datetime, timezone

from dependency_injector.wiring import inject, Provide

from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from .celery_application import celery_app
from .utils import get_discounted_product_collector_service_factory
from ...core.application.use_cases.discounted_product.collect_discounted_products_from_retailer import (
    CollectDiscountedProductsRetailer,
)
from ...core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsRequest


@celery_app.task(name="CollectDiscountedProducts")
async def celery_task_collect_discounted_products_from_all_retailers() -> None:
    await collect_discounted_products_from_all_retailers()


@inject
async def collect_discounted_products_from_all_retailers(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    current_time = datetime.now(timezone.utc)
    use_case_request = CollectDiscountedProductsRequest(started_time=current_time)
    retailer_repo = unit_of_work.retailer_repo
    all_retailers = retailer_repo.get_all()
    tasks = []
    async for retailer in all_retailers:
        discounted_product_collector_factory = await get_discounted_product_collector_service_factory(
            retailer_name=retailer.get_name()
        )
        use_case = CollectDiscountedProductsRetailer(
            unit_of_work=unit_of_work, discounted_product_collector_factory=discounted_product_collector_factory
        )
        tasks.append(use_case.execute(request=use_case_request))

    await asyncio.gather(*tasks)
