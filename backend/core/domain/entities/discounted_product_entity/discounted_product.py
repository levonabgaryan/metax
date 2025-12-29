from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from backend.core.domain.ddd_patterns import AggregateRootEntity, ValueObject
from backend.core.domain.entities.discounted_product_entity.errors.errors import (
    DiscountExceedsRealPriceError,
    NegativePriceError,
)


class DiscountedProduct(AggregateRootEntity):
    def __init__(
        self,
        discounted_product_uuid: UUID,
        category_uuid: UUID | None,
        retailer_uuid: UUID,
        price_details: PriceDetails,
        name: str,
        url: str,
    ) -> None:
        super().__init__(_uuid=discounted_product_uuid)
        self.__category_uuid = category_uuid
        self.__retailer_uuid = retailer_uuid
        self.__price_details = price_details
        self.__name = name
        self.__url = url

    def get_url(self) -> str:
        return self.__url

    def get_category_uuid(self) -> UUID:
        if self.__category_uuid is None:
            raise AttributeError(f"DiscountedProduct {self.get_uuid()} doesn't have a category assigned.")
        return self.__category_uuid

    def get_retailer_uuid(self) -> UUID:
        return self.__retailer_uuid

    def get_name(self) -> str:
        return self.__name

    def get_real_price(self) -> Decimal:
        return self.__price_details.real_price

    def get_discounted_price(self) -> Decimal:
        return self.__price_details.discounted_price

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


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class PriceDetails(ValueObject):
    real_price: Decimal
    discounted_price: Decimal

    def __post_init__(self) -> None:
        self.__validate_real_price()
        self.__validate_discounted_price()
        self.__validate_discount_is_less_than_real()

    def __validate_real_price(self) -> None:
        if self.real_price < Decimal("0.00"):
            raise NegativePriceError(incorrect_price=self.real_price, price_type="Real price")

    def __validate_discounted_price(self) -> None:
        if self.discounted_price < Decimal("0.00"):
            raise NegativePriceError(incorrect_price=self.discounted_price, price_type="Discounted price")

    def __validate_discount_is_less_than_real(self) -> None:
        if not self.discounted_price < self.real_price:
            raise DiscountExceedsRealPriceError(
                discounted_price=self.discounted_price,
                real_price=self.real_price,
            )
