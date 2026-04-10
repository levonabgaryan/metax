from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import override
from uuid import UUID

from metax.core.domain.ddd_patterns import AggregateRootEntity
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails


class DiscountedProduct(AggregateRootEntity):
    def __init__(
        self,
        discounted_product_uuid: UUID,
        category_uuid: UUID | None,
        retailer_uuid: UUID,
        price_details: PriceDetails,
        name: str,
        url: str,
        created_at: datetime,
    ) -> None:
        super().__init__(uuid_=discounted_product_uuid)
        self.__category_uuid = category_uuid
        self.__retailer_uuid = retailer_uuid
        self.__price_details = price_details
        self.__name = name
        self.__url = url
        self.__created_at = created_at

    def get_url(self) -> str:
        return self.__url

    def get_category_uuid(self) -> UUID:
        if self.__category_uuid is None:
            msg = f"DiscountedProduct {self.get_uuid()} doesn't have a category assigned."
            raise AttributeError(msg)
        return self.__category_uuid

    def get_retailer_uuid(self) -> UUID:
        return self.__retailer_uuid

    def set_retailer_uuid(self, retailer_uuid: UUID) -> None:
        self.__retailer_uuid = retailer_uuid

    def get_name(self) -> str:
        return self.__name

    def set_name(self, name: str) -> None:
        self.__name = name

    def get_price_details(self) -> PriceDetails:
        return self.__price_details

    def set_price_details(self, price_details: PriceDetails) -> None:
        self.__price_details = price_details

    def get_real_price(self) -> Decimal:
        return self.__price_details.real_price

    def get_discounted_price(self) -> Decimal:
        return self.__price_details.discounted_price

    def has_category(self) -> bool:
        return self.__category_uuid is not None

    def get_created_at(self) -> datetime:
        return self.__created_at

    def set_created_at(self, created_at: datetime) -> None:
        self.__created_at = created_at

    @override
    def __str__(self) -> str:
        return (
            f"DiscountedProduct(\n"
            f"  uuid={self.get_uuid()},\n"
            f"  name='{self.__name}',\n"
            f"  price={self.get_discounted_price()} (old: {self.get_real_price()}),\n"
            f"  retailer_uuid={self.__retailer_uuid},\n"
            f"  category_uuid={self.__category_uuid},\n"
            f"  url='{self.__url}'\n"
            f")"
        )

    def set_category_uuid(self, category_uuid: UUID | None) -> None:
        self.__category_uuid = category_uuid

    def set_url(self, url: str) -> None:
        self.__url = url
