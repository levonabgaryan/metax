from datetime import datetime, timezone
import pytest

from discount_service.core.application.ports.patterns.unit_of_work import UnitOfWork
from discount_service.core.application.ports.repositories.category import CategoryFieldsToUpdate
from discount_service.core.domain.entities.category_entity.category import DataForCategoryUpdate
from discount_service.core.domain.entities.category_entity.events import CategoryUpdated
from discount_service.frameworks_and_drivers.di.event_handlers_container import CategoryEventHandlersContainer
from tests.integration.conftest import make_category_entity, make_retailer_entity, make_discounted_product_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_event_handler_shall_update_category_in_read_model(
    unit_of_work: UnitOfWork, category_event_handlers: CategoryEventHandlersContainer
) -> None:
    # given
    category = make_category_entity(name="test_name")
    retailer = make_retailer_entity()
    discounted_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), category_uuid=category.get_uuid()
    )
    creation_date = datetime.now(tz=timezone.utc)

    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.repositories.retailer.add(retailer)
        await uow.repositories.discounted_product.add_many_by_date(
            discounted_products=[discounted_product], started_time=creation_date
        )
        await uow.commit()

    async with unit_of_work as uow:
        found_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        new_data = DataForCategoryUpdate(new_name="test_new_name")
        found_category.update(new_data)
        fields_to_update = CategoryFieldsToUpdate(name=True)
        await uow.repositories.category.update(found_category, fields_to_update=fields_to_update)
        await uow.commit()

    event = CategoryUpdated(
        category_uuid=found_category.get_uuid(),
    )
    event_handler = category_event_handlers.update_discounted_product_read_model()

    # when
    await event_handler.handle(event)

    # then
    async with unit_of_work as uow:
        updated_category = await uow.repositories.category.get_by_uuid(category.get_uuid())
        await uow.commit()

    assert updated_category.get_name() == "test_new_name"
