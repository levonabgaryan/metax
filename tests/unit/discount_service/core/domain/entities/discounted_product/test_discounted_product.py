import pytest

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import PriceDetails
from decimal import Decimal

from discount_service.core.domain.entities.discounted_product_entity.errors.errors import (
    NegativePriceError,
    DiscountExceedsRealPriceError,
)


def test_negative_price() -> None:
    # given
    real_price = Decimal("-1")
    discounted_price = Decimal("-2")

    # when
    with pytest.raises(NegativePriceError) as err:
        PriceDetails(real_price=real_price, discounted_price=discounted_price)

    # then
    assert err.value.message == "Real price cannot be negative."
    assert err.value.details == {"price_type": "Real price", "incorrect_price": str(-1)}


def test_discount_exceeds_real_price() -> None:
    # given
    real_price = Decimal("1")
    discounted_price = Decimal("2")

    # when
    with pytest.raises(DiscountExceedsRealPriceError) as err:
        PriceDetails(real_price=real_price, discounted_price=discounted_price)
    # then
    assert err.value.message == "Discounted price (2) cannot exceed the real price (1)."
