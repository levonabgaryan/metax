from datetime import datetime, timezone, timedelta

import pytest

from backend.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from backend.frameworks_and_drivers.di.event_handlers_container import DiscountedProductEventHandlersContainer
from tests.integration.conftest import make_discounted_product_entity, make_retailer_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_delete_old_data(
    unit_of_work: UnitOfWork, discounted_product_event_handlers: DiscountedProductEventHandlersContainer
) -> None:
    # given
    retailer = make_retailer_entity()
    old_discounted_product = make_discounted_product_entity(retailer_uuid=retailer.get_uuid())
    old_discounted_product_created_date = datetime.now(timezone.utc)

    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.repositories.discounted_product.add_many_by_date(
            [old_discounted_product], old_discounted_product_created_date
        )
        await uow.commit()

    async with unit_of_work as uow:
        discounted_product = await uow.repositories.discounted_product.get_by_uuid(
            old_discounted_product.get_uuid()
        )
        await uow.commit()
        assert discounted_product.get_uuid() == old_discounted_product.get_uuid()

    new_products_created_date = old_discounted_product_created_date + timedelta(days=1)
    event = NewDiscountedProductsFromRetailerCollected(new_products_created_date)

    # when
    event_handler = discounted_product_event_handlers.delete_old_discounted_products()
    await event_handler.handle(event)

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.repositories.discounted_product.get_by_uuid(old_discounted_product.get_uuid())
        await uow.commit()
