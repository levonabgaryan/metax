from datetime import datetime, timezone

import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.event_and_handlers.discounted_product.events import (
    OldDiscountedProductsDeleted,
)
from discount_service.core.application.event_and_handlers.discounted_product.sync_discounted_products_read_model import (
    SyncDiscountedProductReadModel,
)
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork

from discount_service.core.application.read_models.discounted_product import DiscountedProductReadModel
from discount_service.frameworks_and_drivers.di.boostrap import ServiceContainer
from discount_service.frameworks_and_drivers.opensearch.indices import discounted_product_read_model
from tests.utils import (
    make_retailer_entity,
    make_discounted_product_entity,
    clear_opensearch_db,
    refresh_opensearch_index,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@clear_opensearch_db
@inject
async def test_event_handler_shall_save_in_empty_read_model(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
    event_handler_: SyncDiscountedProductReadModel = Provide[
        ServiceContainer.event_handlers_container.container.discounted_product.container.sync_discounted_product_read_model
    ],
) -> None:
    # given
    creation_data = datetime.now(tz=timezone.utc)
    retailer = make_retailer_entity()
    discounted_products = [
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid(), created_at=creation_data),
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid(), created_at=creation_data),
    ]
    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many(discounted_products)
        await uow.commit()

    discounted_product_read_models_: list[DiscountedProductReadModel] = []
    for product in discounted_products:
        discounted_product_read_models_.append(
            DiscountedProductReadModel(
                discounted_product_uuid=str(product.get_uuid()),
                name=product.get_name(),
                real_price=float(product.get_real_price()),
                discounted_price=float(product.get_discounted_price()),
                retailer_uuid=str(product.get_retailer_uuid()),
                retailer_name=retailer.get_name(),
                created_at=product.get_created_at().isoformat(),
            )
        )

    await unit_of_work.discounted_product_read_model_repo.add_many(discounted_product_read_models_)

    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)
    event = OldDiscountedProductsDeleted(
        new_discounted_products_creation_date=creation_data,
    )
    event_handler = event_handler_

    # when
    await event_handler.handle(event)

    # then
    await refresh_opensearch_index(index_or_alias_name=discounted_product_read_model.ALIAS_NAME)
    assert await uow.discounted_product_read_model_repo.get_all_count() == 2
    read_model: DiscountedProductReadModel
    async for read_model in uow.discounted_product_read_model_repo.get_all():
        assert read_model["discounted_product_uuid"] in {
            str(product.get_uuid()) for product in discounted_products
        }
        assert read_model["created_at"] == creation_data.isoformat()
