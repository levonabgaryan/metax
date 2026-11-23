from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest

from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax.frameworks_and_drivers.ddd_patterns.services.discounted_product_collector_services.sas_am import (
    SasAmCollectorService,
)
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

    # when (no category classifier — classification is optional and disabled here)
    await collect_discounted_products_from_all_retailers(
        unit_of_work_provider=metax_container.get_unit_of_work_provider(),
        event_bus=event_bus,
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


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_failed_retailer_keeps_previous_set_and_is_left_out_of_publish(
    metax_lifespan_manager_for_tests: MetaxAppLifespanManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given: two retailers with a live set from a previous run; one collector fails mid-crawl after
    # saving a partial batch
    metax_container = metax_lifespan_manager_for_tests.get_metax_container()
    unit_of_work = metax_container.get_unit_of_work()
    started_time = dt.datetime.now(tz=dt.UTC)
    previous_run = started_time - dt.timedelta(days=1)
    healthy = make_retailer_entity(name=RetailersNames.YEREVAN_CITY)
    broken = make_retailer_entity(name=RetailersNames.SAS_AM)
    broken_previous = make_discounted_product_entity(retailer_uuid=broken.get_uuid(), created_at=previous_run)
    # A batch the broken collector already saved in this run before raising.
    broken_partial = make_discounted_product_entity(retailer_uuid=broken.get_uuid(), created_at=started_time)

    async with unit_of_work as uow:
        await uow.retailer_repo.add(healthy)
        await uow.retailer_repo.add(broken)
        await uow.discounted_product_repo.add_many([broken_previous, broken_partial])
        await uow.commit()

    async def healthy_collect(
        self: YerevanCityCollectorService,  # noqa: ARG001
        start_date_of_collecting: dt.datetime,
    ) -> AsyncIterator[DiscountedProduct]:
        yield make_discounted_product_entity(retailer_uuid=healthy.get_uuid(), created_at=start_date_of_collecting)
        await asyncio.sleep(0)

    async def broken_collect(
        self: SasAmCollectorService,  # noqa: ARG001
        start_date_of_collecting: dt.datetime,
    ) -> AsyncIterator[DiscountedProduct]:
        yield make_discounted_product_entity(retailer_uuid=broken.get_uuid(), created_at=start_date_of_collecting)
        await asyncio.sleep(0)
        msg = "site layout changed"
        raise RuntimeError(msg)

    monkeypatch.setattr(YerevanCityCollectorService, "collect", healthy_collect)
    monkeypatch.setattr(SasAmCollectorService, "collect", broken_collect)

    # when
    collected = await collect_discounted_products_from_all_retailers(
        unit_of_work_provider=metax_container.get_unit_of_work_provider(),
        event_bus=await metax_container.get_event_bus(),
        start_date_of_collecting=started_time,
    )

    # then: only the healthy retailer is published, and the broken one's partial rows are discarded so
    # exactly its previous set remains
    assert collected == [healthy.get_uuid()]
    async with unit_of_work as uow:
        remaining = [product async for product in uow.discounted_product_repo.all()]
    broken_rows = [product for product in remaining if product.get_retailer_uuid() == broken.get_uuid()]
    assert [product.get_uuid() for product in broken_rows] == [broken_previous.get_uuid()]
