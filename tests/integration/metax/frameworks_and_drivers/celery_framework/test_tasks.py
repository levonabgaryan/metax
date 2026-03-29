import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncIterator

import pytest
from celery.schedules import crontab

from metax.core.domain.entities.discounted_product.entity import DiscountedProduct
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails
from metax.frameworks_and_drivers.celery_framework.tasks import (
    collect_discounted_products_from_all_retailers,
)
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.yerevan_city import (
    YerevanCityCollectorService,
)
from metax.frameworks_and_drivers.di.metax_container import MetaxContainer

from metax.core.domain.entities.retailer.value_objects import RetailersNames
from tests.utils import make_retailer_entity, make_discounted_product_entity


def test_collect_products_task_schedule() -> None:
    from metax.frameworks_and_drivers.celery_framework.celery_application import celery_app

    task_name = "run-daily-task-at-0100"

    assert task_name in celery_app.conf.beat_schedule

    schedule_entry = celery_app.conf.beat_schedule[task_name]

    assert schedule_entry["task"] == "CollectDiscountedProducts"

    schedule = schedule_entry["schedule"]
    assert isinstance(schedule, crontab)
    assert schedule.hour == {1}  # type: ignore[attr-defined]
    assert schedule.minute == {0}  # type: ignore[attr-defined]


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_collect_discounted_products_from_all_retailers(
    metax_container_for_integration_tests: MetaxContainer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given
    started_time = datetime.now(tz=timezone.utc)
    unit_of_work = await metax_container_for_integration_tests.patterns_container.container.unit_of_work.async_()
    event_bus = metax_container_for_integration_tests.patterns_container.container.event_bus()
    retailer = make_retailer_entity(name=RetailersNames.YEREVAN_CITY)
    await unit_of_work.retailer_repo.add(retailer)

    mock_data = [
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            name="lays",
            created_at=started_time,
            price_details=PriceDetails(discounted_price=Decimal("650"), real_price=Decimal("850.0")),
        ),
        make_discounted_product_entity(
            retailer_uuid=retailer.get_uuid(),
            name="cola",
            created_at=started_time,
            price_details=PriceDetails(discounted_price=Decimal("350"), real_price=Decimal(450)),
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
        self: YerevanCityCollectorService, start_date_of_collecting: datetime
    ) -> AsyncIterator[DiscountedProduct]:
        for p in mock_data:
            yield p
            await asyncio.sleep(0)

    monkeypatch.setattr(YerevanCityCollectorService, "collect", fake_collect)

    # when
    await collect_discounted_products_from_all_retailers(
        unit_of_work_provider=metax_container_for_integration_tests.patterns_container.container.unit_of_work_provider(),
        category_classifier_service=metax_container_for_integration_tests.patterns_container.container.category_classifier_service(),
        start_date_of_collecting=started_time,
        event_bus=event_bus,
    )

    # then
    discounted_products = unit_of_work.discounted_product_repo.get_all()

    count = 0
    async for discounted_product in discounted_products:
        count += 1
        assert discounted_product.get_name() in discounted_product_names
        assert discounted_product.get_url() in discounted_products_urls
        assert discounted_product.get_discounted_price() in discounted_products_discounted_prices
        assert discounted_product.get_real_price() in discounted_products_real_prices

    assert count == 2
