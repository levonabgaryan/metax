from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from metax.core.domain.ddd_patterns import ValueObject
from metax.core.domain.entities.discounted_product.errors import (
    DiscountExceedsRealPriceError,
    NegativePriceError,
)


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class PriceDetails(ValueObject):
    real_price: Decimal
    discounted_price: Decimal

    def __post_init__(self) -> None:
        self.__validate_real_price()
        self.__validate_discounted_price()
        self.__validate_discount_is_less_than_real()

    @classmethod
    def create(cls, real_price: Decimal, discounted_price: Decimal) -> PriceDetails:
        return PriceDetails(
            real_price=cls.__normalize(real_price),
            discounted_price=cls.__normalize(discounted_price),
        )

    def __validate_real_price(self) -> None:
        if self.real_price < Decimal("0.00"):
            raise NegativePriceError(value=self.real_price)

    def __validate_discounted_price(self) -> None:
        if self.discounted_price < Decimal("0.00"):
            raise NegativePriceError(value=self.discounted_price)

    def __validate_discount_is_less_than_real(self) -> None:
        if not self.discounted_price < self.real_price:
            raise DiscountExceedsRealPriceError(
                discounted_price=self.discounted_price,
                real_price=self.real_price,
            )

    @staticmethod
    def __normalize(value: Decimal) -> Decimal:
        """Force 2 decimal places: 12 -> 12.00, 12.5 -> 12.50"""
        return value.quantize(
            Decimal("0.00"),
            rounding=ROUND_HALF_UP,
        )
