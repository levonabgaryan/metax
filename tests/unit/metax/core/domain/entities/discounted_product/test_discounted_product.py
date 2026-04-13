from decimal import Decimal

import pytest
from core.domain.entities.discounted_product.errors import (
    DiscountExceedsRealPriceError,
    NegativePriceError,
)

from metax.core.domain.entities.discounted_product.value_objects import PriceDetails


def test_negative_price() -> None:
    # given
    real_price = Decimal("-1")
    discounted_price = Decimal("-2")

    # when
    with pytest.raises(NegativePriceError) as err:
        PriceDetails(real_price=real_price, discounted_price=discounted_price)

    # then
    assert err.value.title == "Real price cannot be negative."


def test_discount_exceeds_real_price() -> None:
    # given
    real_price = Decimal("1")
    discounted_price = Decimal("2")

    # when
    with pytest.raises(DiscountExceedsRealPriceError) as err:
        PriceDetails(real_price=real_price, discounted_price=discounted_price)
    # then
    assert err.value.title == "Discounted price (2.00) cannot exceed the real price (1.00)."
