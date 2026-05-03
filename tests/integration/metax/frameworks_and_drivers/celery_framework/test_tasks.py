import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from celery.schedules import crontab

from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.frameworks_and_drivers.celery_framework.tasks import (
    collect_discounted_products_from_all_retailers,
)
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.yerevan_city import (
    YerevanCityCollectorService,
)
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_discounted_product_entity, make_retailer_entity


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
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given
    metax_container = metax_lifespan_manager_for_integration_tests.get_metax_container()
    started_time = datetime.now(tz=UTC)
    unit_of_work = metax_container.get_unit_of_work()
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
        start_date_of_collecting: datetime,  # noqa: ARG001
    ) -> AsyncIterator[DiscountedProduct]:
        for p in mock_data:
            yield p
            await asyncio.sleep(0)

    monkeypatch.setattr(YerevanCityCollectorService, "collect", fake_collect)

    # when
    await collect_discounted_products_from_all_retailers(
        unit_of_work_provider=metax_container.get_unit_of_work_provider(),
        category_classifier_service=metax_container.get_category_classifier_service(),
        start_date_of_collecting=started_time,
        event_bus=event_bus,
    )

    # then
    discounted_products = unit_of_work.discounted_product_repo.all()

    count = 0
    async for discounted_product in discounted_products:
        count += 1
        assert discounted_product.get_name() in discounted_product_names
        assert discounted_product.get_url() in discounted_products_urls
        assert discounted_product.get_discounted_price() in discounted_products_discounted_prices
        assert discounted_product.get_real_price() in discounted_products_real_prices

    assert count == 2
