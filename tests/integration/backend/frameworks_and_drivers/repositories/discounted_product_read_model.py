from datetime import datetime, timezone, timedelta

import pytest

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.ports.repositories.category import CategoryFieldsToUpdate
from backend.core.application.ports.repositories.retailer import RetailerFieldsToUpdate
from backend.core.domain.entities.category_entity.category import DataForCategoryUpdate
from backend.core.domain.entities.retailer_entity.retailer import DataForRetailerUpdate
from django_framework.discount_service.models import DiscountedProductReadModel
from tests.integration.conftest import (
    make_retailer_entity,
    make_discounted_product_entity,
    make_discounted_product_django_read_model,
    make_category_entity,
)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_sync_many_by_date(unit_of_work: UnitOfWork) -> None:
    # given
    retailer = make_retailer_entity()
    discounted_products = [
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid()),
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid()),
    ]
    created_at = datetime.now(tz=timezone.utc)
    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.repositories.discounted_product.add_many_by_date(discounted_products, created_at)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        await uow.repositories.discounted_product_read_model.sync_many_by_date(created_at)
        await uow.commit()

    # then
    read_models_query_set = DiscountedProductReadModel._default_manager.all()
    count = await read_models_query_set.acount()
    assert count == 2
    async for product in read_models_query_set.aiterator(chunk_size=100):
        assert product.discounted_product_uuid in {product.get_uuid() for product in discounted_products}
        assert product.created_at == created_at


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_older_than_and_return_deleted_count(unit_of_work: UnitOfWork) -> None:
    # given
    retailer = make_retailer_entity()
    discounted_products = [
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid()),
        make_discounted_product_entity(retailer_uuid=retailer.get_uuid()),
    ]

    creation_date = datetime.now(tz=timezone.utc)
    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer)
        await uow.repositories.discounted_product.add_many_by_date(discounted_products, creation_date)
        await uow.repositories.discounted_product_read_model.sync_many_by_date(creation_date)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        deleted_count = (
            await uow.repositories.discounted_product_read_model.delete_older_than_and_return_deleted_count(
                date_limit=creation_date + timedelta(days=1),
            )
        )
        await uow.commit()

    # then
    assert deleted_count == 2
    read_models_query_set = DiscountedProductReadModel._default_manager.all()
    count = await read_models_query_set.acount()
    assert count == 0


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_category(unit_of_work: UnitOfWork) -> None:
    # given
    created_at = datetime.now(tz=timezone.utc)
    category = make_category_entity()
    read_model = make_discounted_product_django_read_model(created_at=created_at, category=category)
    await read_model.asave()
    async with unit_of_work as uow:
        await uow.repositories.category.add(category=category)
        await uow.commit()

    async with unit_of_work as uow:
        assert read_model.category_uuid is not None
        found_category = await uow.repositories.category.get_by_uuid(read_model.category_uuid)
        assert category.get_name() == read_model.category_name
        new_data = DataForCategoryUpdate(new_name="new_name_123")
        found_category.update(new_data)
        fields_to_update = CategoryFieldsToUpdate(name=True)
        await uow.repositories.category.update(found_category, fields_to_update)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        await uow.repositories.discounted_product_read_model.update_category(found_category)
        await uow.commit()

    # then
    read_model = await DiscountedProductReadModel._default_manager.aget(
        discounted_product_uuid=read_model.discounted_product_uuid
    )
    assert read_model.category_name == "new_name_123"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_update_retailer(unit_of_work: UnitOfWork) -> None:
    # given
    created_at = datetime.now(tz=timezone.utc)
    retailer = make_retailer_entity()
    read_model = make_discounted_product_django_read_model(created_at=created_at, retailer=retailer)
    await read_model.asave()
    async with unit_of_work as uow:
        await uow.repositories.retailer.add(retailer=retailer)
        await uow.commit()

    async with unit_of_work as uow:
        found_retailer = await uow.repositories.retailer.get_by_uuid(read_model.retailer_uuid)
        assert retailer.get_name() == read_model.retailer_name
        new_data = DataForRetailerUpdate(
            new_name="new_name_123",
            new_url="new_url_123",
            new_phone_number="new_phone_number_123",
        )
        found_retailer.update(new_data)
        fields_to_update = RetailerFieldsToUpdate(
            name=True,
            url=True,
            phone_number=True,
        )
        await uow.repositories.retailer.update(found_retailer, fields_to_update)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        await uow.repositories.discounted_product_read_model.update_retailer(found_retailer)
        await uow.commit()

    read_model = await DiscountedProductReadModel._default_manager.aget(
        discounted_product_uuid=read_model.discounted_product_uuid
    )
    assert read_model.retailer_name == "new_name_123"
