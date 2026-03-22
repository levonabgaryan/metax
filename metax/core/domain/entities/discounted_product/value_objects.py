from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from metax.core.domain.ddd_patterns import ValueObject
from metax.core.domain.entities.discounted_product.errors.errors import (
    NegativePriceError,
    DiscountExceedsRealPriceError,
)


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class PriceDetails(ValueObject):
    real_price: Decimal
    discounted_price: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "real_price",
            self.__normalize(self.real_price),
        )

        object.__setattr__(
            self,
            "discounted_price",
            self.__normalize(self.discounted_price),
        )
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

    @staticmethod
    def __normalize(value: Decimal) -> Decimal:
        """
        Force 2 decimal places: 12 -> 12.00, 12.5 -> 12.50
        """

        return value.quantize(
            Decimal("0.00"),
            rounding=ROUND_HALF_UP,
        )
