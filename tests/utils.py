import asyncio
import datetime as dt
from collections.abc import AsyncIterator, Iterable, Iterator
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar, override
from uuid import UUID, uuid7

from metax.core.application.ports.ddd_patterns.service.discounted_product_collector_service import (
    DiscountedProductCollectorService,
)
from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.application.read_models.discounted_product import (
    DiscountedProductCategoryReadModel,
    DiscountedProductReadModel,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.category_helper_word.entity import CategoryHelperWord
from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def make_category_entity(
    category_uuid: UUID | None = None,
    name: str = "test_category_name",
    helper_words: list[CategoryHelperWord] | None = None,
    created_at: dt.datetime | None = None,
    updated_at: dt.datetime | None = None,
) -> Category:
    now = dt.datetime.now(tz=dt.UTC)
    created = created_at or now
    updated = updated_at or (created + dt.timedelta(seconds=1))

    return Category(
        name=name,
        uuid_=category_uuid or uuid7(),
        helper_words=helper_words
        if helper_words is not None
        else [
            CategoryHelperWord(
                uuid_=uuid7(),
                created_at=created,
                updated_at=updated,
                helper_word_text="test_word1",
            ),
            CategoryHelperWord(
                uuid_=uuid7(),
                created_at=created,
                updated_at=updated,
                helper_word_text="test_word2",
            ),
        ],
        created_at=created,
        updated_at=updated,
    )


def make_helper_word_entity(
    uuid_: UUID | None = None,
    created_at: dt.datetime | None = None,
    updated_at: dt.datetime | None = None,
    helper_word_text: str | None = None,
) -> CategoryHelperWord:

    uuid_ = uuid_ or uuid7()
    created_at = created_at or dt.datetime.now(tz=dt.UTC)
    updated_at = updated_at or (created_at + dt.timedelta(seconds=1))
    helper_word_text = helper_word_text or "test_word"
    return CategoryHelperWord(
        uuid_=uuid_,
        created_at=created_at,
        updated_at=updated_at,
        helper_word_text=helper_word_text,
    )


def make_retailer_entity(
    retailer_uuid: UUID | None = None,
    name: str = RetailersNames.YEREVAN_CITY,
    url: str = "test_retailer_url",
    phone_number: str = "test_retailer_phone_number",
    created_at: dt.datetime | None = None,
    updated_at: dt.datetime | None = None,
) -> Retailer:
    now = dt.datetime.now(tz=dt.UTC)
    created = created_at or now
    updated = updated_at or (created + dt.timedelta(seconds=1))
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
    created_at: dt.datetime,
    category_uuid: UUID | None = None,
    discounted_product_uuid: UUID | None = None,
    name: str = "test_discounted_product_name",
    real_price: Decimal = Decimal(100),
    discounted_price: Decimal = Decimal(50),
    url: str = "test_discounted_product_url",
    updated_at: dt.datetime | None = None,
) -> DiscountedProduct:
    updated = updated_at or (created_at + dt.timedelta(seconds=1))
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
    created_at: dt.datetime,
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
    created_iso = created_at.isoformat()
    updated_iso = (created_at + dt.timedelta(seconds=1)).isoformat()
    result: DiscountedProductReadModel = {
        "uuid_": discounted_product_uuid,
        "name": name,
        "real_price": real_price,
        "discounted_price": discounted_price,
        "created_at": created_iso,
        "updated_at": updated_iso,
        "url": url,
        "retailer": {
            "uuid_": retailer_uuid,
            "created_at": created_iso,
            "updated_at": updated_iso,
            "name": retailer_name,
            "home_page_url": "https://retailer.com",
            "phone_number": "+37498521474",
        },
    }
    if category_uuid is not None:
        result["category"] = DiscountedProductCategoryReadModel(
            uuid_=category_uuid,
            created_at=created_iso,
            updated_at=updated_iso,
            name=category_name or "test_category_name",
        )
    return result


async def mock_create_many_discounted_products_from_retailer(
    retailer_uuid: UUID, discounted_product_counts: int = 4, batch_size: int = 1
) -> AsyncIterator[list[DiscountedProduct]]:
    # Mock function for IDiscountedProductFactory.create_many_from_retailer
    discounted_products = []
    for _ in range(discounted_product_counts):
        discounted_product = make_discounted_product_entity(
            retailer_uuid=retailer_uuid, created_at=dt.datetime.now(tz=dt.UTC)
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


@dataclass(frozen=True)
class FakeProductSpec:
    """Lightweight description of a product the fake creator should yield."""

    name: str
    real_price: Decimal = Decimal(1000)
    discounted_price: Decimal = Decimal(500)
    url: str = ""


class FakeDiscountedProductsCreator(DiscountedProductCollectorServiceCreator):
    """Yields products stamped with the task's ``start_date_of_collecting``.

    Both the delete-old and sync handlers in the event bus key off that timestamp
    (delete: ``created_at < date_limit``; sync: ``created_at == date_limit``),
    so products MUST be stamped with the same instant the task started.
    """

    SPECS_BY_RETAILER_NAME: ClassVar[dict[str, list[FakeProductSpec]]] = {}

    def __init__(self, start_date_of_collecting: dt.datetime, retailer: Retailer) -> None:
        super().__init__(start_date_of_collecting=start_date_of_collecting)
        self._retailer = retailer
        self._start_date_of_collecting = start_date_of_collecting

    @override
    def create_collector_service(self) -> DiscountedProductCollectorService:
        msg = "Fake overrides do_collect directly"
        raise NotImplementedError(msg)

    @override
    async def do_collect(self) -> AsyncIterator[DiscountedProduct]:
        for spec in self.SPECS_BY_RETAILER_NAME.get(self._retailer.get_name(), []):
            yield make_discounted_product_entity(
                retailer_uuid=self._retailer.get_uuid(),
                created_at=self._start_date_of_collecting,
                name=spec.name,
                real_price=spec.real_price,
                discounted_price=spec.discounted_price,
                url=spec.url or f"http://fake/{spec.name.replace(' ', '_')}",
            )
