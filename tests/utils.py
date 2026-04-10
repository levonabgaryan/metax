import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, AsyncIterator, Iterable, Iterator
from uuid import UUID, uuid7

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.core.domain.entities.category.entity import Category
from metax.core.domain.entities.category.value_objects import CategoryHelperWords
from metax.core.domain.entities.discounted_product.entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def make_category_entity(
    category_uuid: UUID | None = None,
    name: str = "test_category_name",
    helper_words: CategoryHelperWords | None = None,
) -> Category:
    if helper_words is None:
        helper_words = CategoryHelperWords(words=frozenset(["test_word1", " test_word2"]))

    return Category(
        name=name,
        category_uuid=category_uuid or uuid7(),
        helper_words=helper_words,
    )


def make_retailer_entity(
    retailer_uuid: UUID | None = None,
    name: RetailersNames = RetailersNames.YEREVAN_CITY,
    url: str = "test_retailer_url",
    phone_number: str = "test_retailer_phone_number",
) -> Retailer:
    return Retailer(
        retailer_uuid=retailer_uuid or uuid7(),
        name=name,
        phone_number=phone_number,
        home_page_url=url,
    )


def make_discounted_product_entity(
    retailer_uuid: UUID,
    created_at: datetime,
    category_uuid: UUID | None = None,
    discounted_product_uuid: UUID | None = None,
    name: str = "test_discounted_product_name",
    price_details: PriceDetails | None = None,
    url: str = "test_discounted_product_url",
) -> DiscountedProduct:
    price_details = price_details or PriceDetails(
        real_price=Decimal("100"),
        discounted_price=Decimal("50"),
    )
    return DiscountedProduct(
        name=name,
        retailer_uuid=retailer_uuid,
        category_uuid=category_uuid,
        discounted_product_uuid=discounted_product_uuid or uuid7(),
        price_details=price_details,
        url=url,
        created_at=created_at,
    )


def make_discounted_product_read_model(
    created_at: datetime,
    discounted_product_uuid: str,
    name: str = "test_discounted_product_name",
    real_price: float = 1000,
    discounted_price: float = 500,
    category_uuid: str | None = None,
    category_name: str | None = None,
    retailer_uuid: str = str(uuid7()),
    retailer_name: str = "test_retailer_name",
    url: str | None = None,
) -> DiscountedProductReadModel:
    return DiscountedProductReadModel(
        discounted_product_uuid=discounted_product_uuid,
        name=name,
        real_price=real_price,
        discounted_price=discounted_price,
        category_uuid=category_uuid,
        category_name=category_name,
        retailer_uuid=retailer_uuid,
        retailer_name=retailer_name,
        url=url,
        created_at=created_at.isoformat(),
    )


async def mock_create_many_discounted_products_from_retailer(
    retailer_uuid: UUID, discounted_product_counts: int = 4, batch_size: int = 1
) -> AsyncIterator[list[DiscountedProduct]]:
    # Mock function for IDiscountedProductFactory.create_many_from_retailer
    discounted_products = []
    for _ in range(discounted_product_counts):
        discounted_product = make_discounted_product_entity(
            retailer_uuid=retailer_uuid, created_at=datetime.now(tz=timezone.utc)
        )
        discounted_products.append(discounted_product)

        if len(discounted_products) == batch_size:
            yield discounted_products
            discounted_products = []
            await asyncio.sleep(0.0)

    if discounted_products:
        yield discounted_products


async def __aiter_wrapper(items: Iterator[Any] | Iterable[Any]) -> AsyncIterator[Any]:
    for item in items:
        yield item
        await asyncio.sleep(0.0)
