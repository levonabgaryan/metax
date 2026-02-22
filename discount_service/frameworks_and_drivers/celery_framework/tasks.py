import asyncio
from datetime import datetime, timezone

from .celery_application import celery_app
from dependency_injector.wiring import inject, Provide

from ..di import ServiceContainer
from ..di.scrappers_adapters_selector_container import ScrappersAdaptersSelectorContainer
from ..patterns.services.discounted_products_collector_services import DiscountedProductsCollectorServiceFromRetailer
from ..scrappers_adapters.scrapper_adapter import ScrapperAdapter
from ...core.application.patterns.category_classifier_service import CategoryClassifierService
from ...core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from ...core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
from ...core.application.use_cases.discounted_product.collect_discounted_products import CollectDiscountedProducts
from ...core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsRequest
from ...core.domain.entities.retailer_entity.retailer import Retailer
from constants import RetailersNames


@celery_app.task(name="CollectDiscountedProducts")
@inject
async def celery_task_collect_discounted_products_from_all_retailers(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    scrappers_adapters_selector_container: ScrappersAdaptersSelectorContainer = Provide[ServiceContainer.scrappers_adapters_selector_container],
        category_classifier_service: CategoryClassifierService = Provide[ServiceContainer.patterns_container.container.category_classifier_service]
) -> None:
    started_time = datetime.now(tz=timezone.utc)
    tasks = []
    all_retailers = unit_of_work.retailer_repo.get_all()
    async for retailer in all_retailers:
        scrapper_adapter = scrappers_adapters_selector_container.scrapper_adapter(retailer_name=retailer.get_name())
        collector_service = DiscountedProductsCollectorServiceFromRetailer(
            retailer=retailer,
            scrapper_adapter=scrapper_adapter
        )
        use_case_request = CollectDiscountedProductsRequest(started_time=started_time)
        use_case = CollectDiscountedProducts(
            unit_of_work=unit_of_work,
            discounted_product_collector_service=collector_service,
            category_classifier_service=category_classifier_service
        )
        tasks.append(use_case.execute(request=use_case_request))
    await asyncio.gather(*tasks)
