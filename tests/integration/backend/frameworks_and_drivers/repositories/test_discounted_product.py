from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.ports.repositories.errors.errors import EntityIsNotFoundError
from backend.core.domain.entities.category_entity.category import Category, CategoryHelperWords
from backend.core.domain.entities.discounted_product_entity.discounted_product import (
    DiscountedProduct,
    PriceDetails,
)
from backend.core.domain.entities.retailer_entity.retailer import Retailer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_add_many_discounted_products(unit_of_work: UnitOfWork) -> None:
    # given
    category_uuid = uuid4()
    helper_words = CategoryHelperWords(words=frozenset(["օղի", "գինի"]))
    category = Category(category_uuid=category_uuid, name="Ալկոհոլ", helper_words=helper_words)

    sas_supermarket_uuid = uuid4()
    retailer = Retailer(
        retailer_uuid=sas_supermarket_uuid,
        name="SAS-SUPERMARKET",
        phone_number="test_phone_number",
        url="test_url",
    )

    discounted_product_1_uuid = uuid4()
    absolut_vodka = DiscountedProduct(
        name="«Absolut» 0.7լ",
        category_uuid=category.get_uuid(),
        retailer_uuid=retailer.get_uuid(),
        url="test_url_1",
        price_details=PriceDetails(discounted_price=Decimal("7500.00"), real_price=Decimal("8390.00")),
        discounted_product_uuid=discounted_product_1_uuid,
    )

    discounted_product_2_uuid = uuid4()
    karas_whine = DiscountedProduct(
        name="Փրփրուն գինի «Կարաս» 0.75լ",
        category_uuid=category.get_uuid(),
        retailer_uuid=retailer.get_uuid(),
        url="test_url_2",
        price_details=PriceDetails(discounted_price=Decimal("4950.00"), real_price=Decimal("5680.00")),
        discounted_product_uuid=discounted_product_2_uuid,
    )

    discounted_products = [absolut_vodka, karas_whine]

    async with unit_of_work as uow:
        await uow.repositories.category.add(category)
        await uow.repositories.retailer.add(retailer)
        await uow.commit()

    # when
    started_time = datetime.now()
    async with unit_of_work as uow:
        await uow.repositories.discounted_product.add_many(discounted_products, started_time)
        await uow.commit()

    # then
    async with unit_of_work as uow:
        added_absolut_vodka = await uow.repositories.discounted_product.get_by_uuid(discounted_product_1_uuid)
        added_karas_whine = await uow.repositories.discounted_product.get_by_uuid(discounted_product_2_uuid)
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
async def test_discounted_products_is_not_found_by_uuid(unit_of_work: UnitOfWork) -> None:
    # given
    random_uuid = uuid4()
    # expect
    async with unit_of_work as uow:
        with pytest.raises(EntityIsNotFoundError) as err:
            await uow.repositories.discounted_product.get_by_uuid(random_uuid)

    # then
    assert (
        err.value.message
        == f"There is no discounted_product entity found by field 'uuid' with value '{random_uuid}'."
    )
    assert err.value.error_code == "DISCOUNTED_PRODUCT_IS_NOT_FOUND"
    assert err.value.details == {"searched_field_name": "uuid", "searched_field_value": f"{random_uuid}"}
