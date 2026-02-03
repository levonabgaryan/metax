import asyncio
import functools
from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncIterator, Callable, Awaitable
from uuid import UUID, uuid4

from dependency_injector.wiring import inject, Provide
from opensearchpy import AsyncOpenSearch

from discount_service.core.application.read_models.discounted_product import DiscountedProductReadModel
from discount_service.core.domain.entities.category_entity.category import CategoryHelperWords, Category
from discount_service.core.domain.entities.discounted_product_entity.discounted_product import (
    PriceDetails,
    DiscountedProduct,
)
from discount_service.core.domain.entities.retailer_entity.retailer import Retailer
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from tests.integration.conftest import get_current_container


def make_category_entity(
    category_uuid: UUID | None = None,
    name: str = "test_category_name",
    helper_words: CategoryHelperWords = CategoryHelperWords(words=frozenset(["test_word1", " test_word2"])),
) -> Category:
    return Category(
        name=name,
        category_uuid=category_uuid or uuid4(),
        helper_words=helper_words,
    )


def make_retailer_entity(
    retailer_uuid: UUID | None = None,
    name: str = "test_retailer_name",
    url: str = "test_retailer_url",
    phone_number: str = "test_retailer_phone_number",
) -> Retailer:
    return Retailer(retailer_uuid=retailer_uuid or uuid4(), name=name, phone_number=phone_number, url=url)


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
        discounted_product_uuid=discounted_product_uuid or uuid4(),
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
    retailer_uuid: str = str(uuid4()),
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
    for i in range(discounted_product_counts):
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


def clear_opensearch_db[T, **P](func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        client: AsyncOpenSearch = await get_current_container().opensearch_async_client.async_()

        indices = await client.indices.get(index="*")
        user_indices = [idx for idx in indices if not idx.startswith(".")]

        if user_indices:
            await client.delete_by_query(
                index=user_indices,
                body={"query": {"match_all": {}}},
                refresh=True,
                wait_for_completion=True,
            )

        try:
            return await func(*args, **kwargs)
        finally:
            indices = await client.indices.get(index="*")
            user_indices = [idx for idx in indices if not idx.startswith(".")]
            if user_indices:
                await client.delete_by_query(
                    index=user_indices,
                    body={"query": {"match_all": {}}},
                    refresh=True,
                    wait_for_completion=True,
                )

    return wrapper


@inject
async def refresh_opensearch_index(
    index_or_alias_name: str,
    opensearch_async_client_: AsyncOpenSearch = Provide[ServiceContainer.opensearch_async_client],
) -> None:
    response = await opensearch_async_client_.indices.refresh(index=index_or_alias_name)
    is_refreshed = int(response["_shards"]["successful"]) != 0
    assert is_refreshed
