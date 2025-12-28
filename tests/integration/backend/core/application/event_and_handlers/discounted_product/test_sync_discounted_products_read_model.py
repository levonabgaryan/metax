from datetime import datetime, timezone

import pytest

from backend.core.application.event_and_handlers.discounted_product.events import OldDiscountedProductsDeleted
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.frameworks_and_drivers.di.event_handlers_container import DiscountedProductEventHandlersContainer
from django_framework.discount_service.models import DiscountedProductReadModel
from tests.integration.conftest import make_retailer_entity, make_discounted_product_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_save_in_empty_read_model(
    unit_of_work: UnitOfWork, discounted_product_event_handlers: DiscountedProductEventHandlersContainer
) -> None:
    # given
    retailer = make_retailer_entity()
    discounted_products = [
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid()),
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid()),
    ]
    creation_data = datetime.now(tz=timezone.utc)

    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.repositories.discounted_product.add_many(discounted_products, creation_data)
        await uow.commit()

    event = OldDiscountedProductsDeleted(
        new_discounted_products_creation_date=creation_data,
    )
    event_handler = discounted_product_event_handlers.sync_discounted_product_read_model()

    # when
    await event_handler.handle(event)

    # then
    queryset = DiscountedProductReadModel._default_manager.all()
    count = await queryset.acount()
    assert count == 2
    async for product in queryset.aiterator(chunk_size=100):
        assert product.created_at == creation_data
