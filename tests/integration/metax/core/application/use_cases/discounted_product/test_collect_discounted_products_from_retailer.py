from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from metax.core.application.ports.ddd_patterns.service.discounted_product_collector_service import (
    DiscountedProductCollectorService,
)
from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.application.use_cases.discounted_product.collect_discounted_products import (
    CollectDiscountedProducts,
)
from metax.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsRequest,
)
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_discounted_product_entity, make_retailer_entity


class _FakeDiscountedProductsCreator(DiscountedProductCollectorServiceCreator):
    def __init__(self, started_at: datetime, items: list[DiscountedProduct]) -> None:
        super().__init__(start_date_of_collecting=started_at)
        self._items = items

    @override
    def create_collector_service(self) -> DiscountedProductCollectorService:  # pragma: no cover
        raise NotImplementedError

    @override
    async def do_collect(self) -> AsyncIterator[DiscountedProduct]:
        for item in self._items:
            yield item


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_collect_discounted_products_use_case_saves_products_in_db(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container.patterns_container.container.unit_of_work()
    started_at = datetime.now(tz=UTC)
    retailer = make_retailer_entity()

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    products_to_collect = [
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            created_at=started_at,
            name="lays",
            url="http://test.com/1",
        ),
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            created_at=started_at,
            name="cola",
            url="http://test.com/2",
        ),
    ]
    creator = _FakeDiscountedProductsCreator(started_at=started_at, items=products_to_collect)

    category_classifier = metax_container.patterns_container.container.category_classifier_service()
    monkeypatch.setattr(category_classifier, "classify_category", AsyncMock(return_value=None))
    event_bus = await metax_container.patterns_container.container.event_bus.async_()

    use_case = CollectDiscountedProducts(
        unit_of_work_provider=metax_container.patterns_container.container.unit_of_work_provider(),
        event_bus=event_bus,
        discounted_product_collector_service_creator=creator,
        category_classifier_service=category_classifier,
        batch_size_for_saving_discounted_products=1,
    )

    # when
    response = await use_case.handle_use_case(
        CollectDiscountedProductsRequest(start_date_of_collecting=started_at)
    )

    # then
    assert response.added_count == 2
    async with unit_of_work as uow:
        saved_products = [p async for p in uow.discounted_product_repo.get_all()]

    assert len(saved_products) == 2
    assert {p.get_name() for p in saved_products} == {"lays", "cola"}
    assert {p.get_url() for p in saved_products} == {"http://test.com/1", "http://test.com/2"}
