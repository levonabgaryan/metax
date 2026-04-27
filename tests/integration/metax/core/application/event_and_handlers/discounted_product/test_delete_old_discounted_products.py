from datetime import UTC, datetime, timedelta

import pytest

from metax.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from metax.core.application.ports.ddd_patterns.repository.errors import EntityIsNotFoundError
from metax_lifespan import MetaxAppLifespanManager
from tests.utils import make_discounted_product_entity, make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_delete_old_data(
    metax_lifespan_manager_for_integration_tests: MetaxAppLifespanManager,
) -> None:
    # given
    metax_container_for_integration_tests = metax_lifespan_manager_for_integration_tests.get_di_container()
    unit_of_work = metax_container_for_integration_tests.patterns_container.container.unit_of_work()
    event_bus = await metax_container_for_integration_tests.resources_container.container.event_bus.async_()
    retailer = make_retailer_entity()
    old_discounted_product_created_date = datetime.now(UTC)
    old_discounted_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), created_at=old_discounted_product_created_date
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([old_discounted_product])
        await uow.commit()

    async with unit_of_work as uow:
        discounted_product = await uow.discounted_product_repo.get_by_uuid(old_discounted_product.get_uuid())
        await uow.commit()
        assert discounted_product.get_uuid() == old_discounted_product.get_uuid()

    new_products_created_date = old_discounted_product_created_date + timedelta(days=1)
    event = NewDiscountedProductsFromRetailerCollected(new_products_created_date)

    # when
    await event_bus.emit(event)

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.discounted_product_repo.get_by_uuid(old_discounted_product.get_uuid())
        await uow.commit()
