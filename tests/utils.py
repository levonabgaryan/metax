import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, AsyncIterator, Iterable, Iterator
from uuid import UUID, uuid7

from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.core.domain.entities.category.entity import Category
from metax.core.domain.entities.discounted_product.entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def make_category_entity(
    category_uuid: UUID | None = None,
    name: str = "test_category_name",
    helper_words: frozenset[str] | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Category:
    now = datetime.now(tz=timezone.utc)
    created = created_at or now
    updated = updated_at or (created + timedelta(seconds=1))

    return Category(
        name=name,
        uuid_=category_uuid or uuid7(),
        helper_words=helper_words if helper_words is not None else frozenset(["test_word1", "test_word2"]),
        created_at=created,
        updated_at=updated,
    )


def make_retailer_entity(
    retailer_uuid: UUID | None = None,
    name: str = RetailersNames.YEREVAN_CITY,
    url: str = "test_retailer_url",
    phone_number: str = "test_retailer_phone_number",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Retailer:
    now = datetime.now(tz=timezone.utc)
    created = created_at or now
    updated = updated_at or (created + timedelta(seconds=1))
    return Retailer(
        uuid_=retailer_uuid or uuid7(),
        name=name,
        phone_number=phone_number,
        home_page_url=url,
        created_at=created,
        updated_at=updated,
    )


def make_discounted_product_entity(
    retailer_uuid: UUID,
    created_at: datetime,
    category_uuid: UUID | None = None,
    discounted_product_uuid: UUID | None = None,
    name: str = "test_discounted_product_name",
    real_price: Decimal = Decimal("100"),
    discounted_price: Decimal = Decimal("50"),
    url: str = "test_discounted_product_url",
    updated_at: datetime | None = None,
) -> DiscountedProduct:
    updated = updated_at or (created_at + timedelta(seconds=1))
    return DiscountedProduct(
        name=name,
        retailer_uuid=retailer_uuid,
        category_uuid=category_uuid,
        uuid_=discounted_product_uuid or uuid7(),
        real_price=real_price,
        discounted_price=discounted_price,
        url=url,
        created_at=created_at,
        updated_at=updated,
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
    url: str = "test_url",
) -> DiscountedProductReadModel:
    result = DiscountedProductReadModel(
        uuid_=discounted_product_uuid,
        name=name,
        real_price=real_price,
        discounted_price=discounted_price,
        retailer_uuid=retailer_uuid,
        retailer_name=retailer_name,
        url=url,
        created_at=created_at.isoformat(),
    )
    if category_uuid is not None:
        result["category_uuid"] = category_uuid
    if category_name is not None:
        result["category_name"] = category_name
    return result


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
