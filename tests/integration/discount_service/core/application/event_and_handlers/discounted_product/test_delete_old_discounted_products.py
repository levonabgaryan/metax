from datetime import datetime, timezone, timedelta

import pytest
from dependency_injector.wiring import inject, Provide

from discount_service.core.application.event_and_handlers.discounted_product.delete_old_discounted_products import (
    DeleteOldDiscountedProducts,
)
from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_retailer_entity, make_discounted_product_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_event_handler_shall_delete_old_data(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    event_handler: DeleteOldDiscountedProducts = Provide[
        ServiceContainer.event_handlers_container.container.discounted_product.container.delete_old_discounted_products
    ],
) -> None:
    # given
    retailer = make_retailer_entity()
    old_discounted_product_created_date = datetime.now(timezone.utc)
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
    event_handler_ = event_handler
    await event_handler_.handle(event)

    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError):
            await uow.discounted_product_repo.get_by_uuid(old_discounted_product.get_uuid())
        await uow.commit()
