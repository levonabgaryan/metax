import datetime as dt
from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, override
from uuid import UUID, uuid7

from metax.core.application.ports.ddd_patterns.service.discounted_product_collector_service import (
    DiscountedProductCollectorService,
)
from metax.core.application.ports.design_patterns.factory.discounted_product_collector_service_creator import (
    DiscountedProductCollectorServiceCreator,
)
from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import (
    DiscountedProduct,
)
from metax.core.domain.entities.retailer.aggregate_root_entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def make_category_entity(
    category_uuid: UUID | None = None,
    name: str = "test_category_name",
    name_hy: str = "",
    name_ru: str = "",
    created_at: dt.datetime | None = None,
    updated_at: dt.datetime | None = None,
) -> Category:
    now = dt.datetime.now(tz=dt.UTC)
    created = created_at or now
    updated = updated_at or (created + dt.timedelta(seconds=1))

    return Category(
        uuid_=category_uuid or uuid7(),
        name=name,
        name_hy=name_hy,
        name_ru=name_ru,
        created_at=created,
        updated_at=updated,
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


@dataclass(frozen=True)
class FakeProductSpec:
    """Lightweight description of a product the fake creator should yield."""

    name: str
    real_price: Decimal = Decimal(1000)
    discounted_price: Decimal = Decimal(500)
    url: str = ""


class FakeDiscountedProductsCreator(DiscountedProductCollectorServiceCreator):
    """Yields products stamped with the task's ``start_date_of_collecting``.

    The delete-old handler in the event bus keys off that timestamp
    (``created_at < date_limit``), so products MUST be stamped with the same instant the task
    started to survive the cleanup and then get embedded.
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
