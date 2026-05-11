from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import AsyncIterator
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.yerevan_city import (
    YerevanCityCollectorService,
)
from metax.frameworks_and_drivers.taskiq_framework.tasks import collect_discounted_products_from_all_retailers
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_discounted_product_entity, make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_collect_discounted_products_from_all_retailers_collects_from_each_retailer(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
    started_time = dt.datetime.now(tz=dt.UTC)
    event_bus = await metax_container.get_event_bus()
    retailer = make_retailer_entity(name=RetailersNames.YEREVAN_CITY)

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    mock_data = [
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            name="lays",
            created_at=started_time,
            real_price=Decimal("850.0"),
            discounted_price=Decimal(650),
        ),
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            name="cola",
            created_at=started_time,
            real_price=Decimal(450),
            discounted_price=Decimal(350),
        ),
    ]
    discounted_product_names = {mock_data[0].get_name(), mock_data[1].get_name()}
    discounted_products_real_prices = {mock_data[0].get_real_price(), mock_data[1].get_real_price()}
    discounted_products_discounted_prices = {
        mock_data[0].get_discounted_price(),
        mock_data[1].get_discounted_price(),
    }
    discounted_products_urls = {mock_data[0].get_url(), mock_data[1].get_url()}

    async def fake_collect(
        self: YerevanCityCollectorService,  # noqa: ARG001
        start_date_of_collecting: dt.datetime,  # noqa: ARG001
    ) -> AsyncIterator[DiscountedProduct]:
        for discounted_product_ in mock_data:
            yield discounted_product_
            await asyncio.sleep(0)

    monkeypatch.setattr(YerevanCityCollectorService, "collect", fake_collect)

    category_classifier = metax_container.get_category_classifier_service()
    monkeypatch.setattr(category_classifier, "classify_category", AsyncMock(return_value=None))

    # when
    await collect_discounted_products_from_all_retailers(
        unit_of_work_provider=metax_container.get_unit_of_work_provider(),
        event_bus=event_bus,
        category_classifier_service=category_classifier,
        start_date_of_collecting=started_time,
    )

    # then
    async with unit_of_work as uow:
        discounted_products = uow.discounted_product_repo.all()
        count = 0
        async for discounted_product in discounted_products:
            count += 1
            assert discounted_product.get_name() in discounted_product_names
            assert discounted_product.get_url() in discounted_products_urls
            assert discounted_product.get_discounted_price() in discounted_products_discounted_prices
            assert discounted_product.get_real_price() in discounted_products_real_prices

    assert count == 2
