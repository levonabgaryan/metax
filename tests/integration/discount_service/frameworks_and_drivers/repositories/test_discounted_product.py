from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from discount_service.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from discount_service.core.domain.entities.category_entity.category import Category, CategoryHelperWords
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.utils import make_retailer_entity, make_discounted_product_entity


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_many_discounted_products(service_container_for_tests: ServiceContainer) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    created_data = datetime.now(tz=timezone.utc)
    category_uuid = uuid4()
    helper_words = CategoryHelperWords(words=frozenset(["օղի", "գինի"]))
    category = Category(category_uuid=category_uuid, name="Ալկոհոլ", helper_words=helper_words)

    sas_supermarket_uuid = uuid4()
    retailer = Retailer(
        retailer_uuid=sas_supermarket_uuid,
        name="SAS-SUPERMARKET",
        phone_number="test_phone_number",
        home_page_url="test_url",
    )

    discounted_product_1_uuid = uuid4()
    absolut_vodka = DiscountedProduct(
        name="«Absolut» 0.7լ",
        category_uuid=category.get_uuid(),
        retailer_uuid=retailer.get_uuid(),
        url="test_url_1",
        price_details=PriceDetails(discounted_price=Decimal("7500.00"), real_price=Decimal("8390.00")),
        discounted_product_uuid=discounted_product_1_uuid,
        created_at=created_data,
    )

    discounted_product_2_uuid = uuid4()
    karas_whine = DiscountedProduct(
        name="Փրփրուն գինի «Կարաս» 0.75լ",
        category_uuid=category.get_uuid(),
        retailer_uuid=retailer.get_uuid(),
        url="test_url_2",
        price_details=PriceDetails(discounted_price=Decimal("4950.00"), real_price=Decimal("5680.00")),
        discounted_product_uuid=discounted_product_2_uuid,
        created_at=created_data,
    )

    discounted_products = [absolut_vodka, karas_whine]

    async with unit_of_work as uow:
        await uow.category_repo.add(category)
        await uow.retailer_repo.add(retailer)
        await uow.commit()

    # when
    async with unit_of_work as uow:
        await uow.discounted_product_repo.add_many(discounted_products)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        added_absolut_vodka = await uow.discounted_product_repo.get_by_uuid(discounted_product_1_uuid)
        added_karas_whine = await uow.discounted_product_repo.get_by_uuid(discounted_product_2_uuid)
        await uow.commit()

    assert added_absolut_vodka.get_uuid() == discounted_product_1_uuid
    assert added_absolut_vodka.get_name() == "«Absolut» 0.7լ"
    assert added_absolut_vodka.get_real_price() == Decimal("8390.00")
    assert added_absolut_vodka.get_discounted_price() == Decimal("7500.00")
    assert added_absolut_vodka.get_category_uuid() == category_uuid
    assert added_absolut_vodka.get_retailer_uuid() == sas_supermarket_uuid
    assert added_absolut_vodka.get_url() == "test_url_1"

    assert added_karas_whine.get_uuid() == discounted_product_2_uuid
    assert added_karas_whine.get_name() == "Փրփրուն գինի «Կարաս» 0.75լ"
    assert added_karas_whine.get_real_price() == Decimal("5680.00")
    assert added_karas_whine.get_discounted_price() == Decimal("4950.00")
    assert added_karas_whine.get_category_uuid() == category_uuid
    assert added_karas_whine.get_retailer_uuid() == sas_supermarket_uuid
    assert added_karas_whine.get_url() == "test_url_2"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_discounted_products_is_not_found_by_uuid(service_container_for_tests: ServiceContainer) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    random_uuid = uuid4()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.discounted_product_repo.get_by_uuid(random_uuid)

    # then
    assert (
        err.value.message
        == f"There is no discounted_product entity found by field 'uuid' with value '{random_uuid}'."
    )
    assert err.value.error_code == "DISCOUNTED_PRODUCT_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "uuid", "searched_field_value": f"{random_uuid}"}


# get_all
# get_all_by_date


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_delete_older_than_and_return_deleted_count(service_container_for_tests: ServiceContainer) -> None:
    # given
    unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()

    creation_date = datetime.now(tz=timezone.utc)
    retailer = make_retailer_entity()
    discounted_product = make_discounted_product_entity(
        created_at=creation_date, retailer_uuid=retailer.get_uuid()
    )

    async with unit_of_work as uow:
        await uow.retailer_repo.add(retailer)
        await uow.discounted_product_repo.add_many([discounted_product])
        await uow.commit()

    # when
    async with unit_of_work as uow:
        deleted_count = await uow.discounted_product_repo.delete_older_than_and_return_deleted_count(
            date_limit=creation_date + timedelta(hours=1)
        )
        await uow.commit()

    # then
    assert deleted_count == 1
    all_products = [product async for product in uow.discounted_product_repo.get_all()]
    assert len(all_products) == 0
