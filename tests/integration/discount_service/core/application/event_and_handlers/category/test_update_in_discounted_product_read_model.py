from datetime import datetime, timezone
import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.event_and_handlers.category.update_in_discounted_product_read_model import (
    UpdateCategoryInDiscountedProductReadModel,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.ports.repositories.entites_repositories.category import (
    CategoryFieldsToUpdate,
)
from discount_service.core.application.read_models.discounted_product import DiscountedProductReadModel
from discount_service.core.domain.entities.category_entity.category import DataForCategoryUpdate
from discount_service.core.domain.entities.category_entity.events import CategoryUpdated
from discount_service.frameworks_and_drivers.di.boostrap import ServiceContainer
from discount_service.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from tests.utils import (
    make_category_entity,
    make_retailer_entity,
    make_discounted_product_entity,
    clear_opensearch_db,
    refresh_opensearch_index,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@clear_opensearch_db
@inject
async def test_event_handler_shall_update_category_in_read_model(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    event_handler: UpdateCategoryInDiscountedProductReadModel = Provide[
        ServiceContainer.event_handlers_container.container.category.container.update_discounted_product_read_model
    ],
) -> None:
    # given
    creation_date = datetime.now(tz=timezone.utc)

    category = make_category_entity(name="test_name")
    retailer = make_retailer_entity()
    discounted_product = make_discounted_product_entity(
        retailer_uuid=retailer.get_uuid(), category_uuid=category.get_uuid(), created_at=creation_date
    )

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(discounted_products=[discounted_product])
        await uow.commit()

    discounted_product_read_model_ = DiscountedProductReadModel(
        discounted_product_uuid=str(discounted_product.get_uuid()),
        name=discounted_product.get_name(),
        real_price=float(discounted_product.get_real_price()),
        discounted_price=float(discounted_product.get_discounted_price()),
        category_uuid=str(discounted_product.get_category_uuid()),
        category_name=category.get_name(),
        retailer_uuid=str(discounted_product.get_retailer_uuid()),
        retailer_name=retailer.get_name(),
        created_at=discounted_product.get_created_at().isoformat(),
    )
    await unit_of_work.discounted_product_read_model_repo.add_many([discounted_product_read_model_])
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)
    async with unit_of_work as uow:
        found_category = await uow.category_repo.get_by_uuid(category.get_uuid())
        new_data = DataForCategoryUpdate(new_name="test_new_name")
        found_category.update(new_data)
        fields_to_update = CategoryFieldsToUpdate(name=True)
        await uow.category_repo.update(found_category, fields_to_update=fields_to_update)
        await uow.commit()

    event = CategoryUpdated(
        category_uuid=found_category.get_uuid(),
    )
    event_handler_ = event_handler

    # when
    await event_handler_.handle(event)

    # then
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)
    updated_category_in_read_model = await unit_of_work.discounted_product_read_model_repo.get_by_uuid(
        discounted_product_read_model_uuid=str(discounted_product.get_uuid())
    )

    assert updated_category_in_read_model["category_name"] == "test_new_name"
