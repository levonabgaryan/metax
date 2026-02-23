from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from celery.schedules import crontab

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import PriceDetails
from discount_service.frameworks_and_drivers.celery_framework.tasks import (
    collect_discounted_products_from_all_retailers,
)
from discount_service.frameworks_and_drivers.di import ServiceContainer
from tests.utils import make_retailer_entity, __aiter_wrapper, make_discounted_product_entity


def test_collect_products_task_schedule() -> None:
    from discount_service.frameworks_and_drivers.celery_framework.celery_application import celery_app

    task_name = "run-daily-task-at-0100"

    assert task_name in celery_app.conf.beat_schedule

    schedule_entry = celery_app.conf.beat_schedule[task_name]

    assert schedule_entry["task"] == "tasks.collect_discounted_products_from_retailer"

    schedule = schedule_entry["schedule"]
    assert isinstance(schedule, crontab)
    assert schedule.hour == {1}  # type: ignore[attr-defined]
    assert schedule.minute == {0}  # type: ignore[attr-defined]


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_collect_discounted_products_from_all_retailers(
    service_container_for_tests: ServiceContainer,
) -> None:
    # given
    started_time = datetime.now(tz=timezone.utc)
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
    retailer = make_retailer_entity(name="yerevan-city")
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
    yerevan_city_scrapper_adapter_mock = MagicMock()
    yerevan_city_scrapper_adapter_mock.fetch.side_effect = lambda *args, **kwargs: __aiter_wrapper(mock_data)

    discounted_product_names = {mock_data[0].get_name(), mock_data[1].get_name()}
    discounted_products_real_prices = {mock_data[0].get_real_price(), mock_data[1].get_real_price()}
    discounted_products_discounted_prices = {
        mock_data[0].get_discounted_price(),
        mock_data[1].get_discounted_price(),
    }
    discounted_products_urls = {mock_data[0].get_url(), mock_data[1].get_url()}

    # when
    with service_container_for_tests.scrappers_adapters_container.container.yerevan_city_scrapper_adapter.override(
        yerevan_city_scrapper_adapter_mock
    ):
        await collect_discounted_products_from_all_retailers(
            unit_of_work=unit_of_work,
            scrappers_adapters_selector_container=service_container_for_tests.scrappers_adapters_selector_container.container,
            category_classifier_service=await service_container_for_tests.patterns_container.container.category_classifier_service.async_(),
            started_time=started_time,
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
