from decimal import Decimal

import pytest

from constants import ErrorCodes
from metax.core.domain.entities.discounted_product.errors import (
    DiscountExceedsRealPriceError,
    NegativePriceError,
)
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails


def test_negative_price() -> None:
    # given
    real_price = Decimal(-1)
    discounted_price = Decimal(-2)

    # expect
    with pytest.raises(NegativePriceError) as err:
        PriceDetails.create(real_price=real_price, discounted_price=discounted_price)

    # then
    assert err.value.error_code == ErrorCodes.NEGATIVE_PRICE
    assert err.value.title == "Price cannot be negative."
    assert err.value.details == "Received value: -1.00."


def test_discount_exceeds_real_price() -> None:
    # given
    real_price = Decimal(1)
    discounted_price = Decimal(2)

    # expect
    with pytest.raises(DiscountExceedsRealPriceError) as err:
        PriceDetails.create(real_price=real_price, discounted_price=discounted_price)
    # then
    assert err.value.error_code == ErrorCodes.DISCOUNT_EXCEEDS_PRICE
    assert err.value.title == "Discounted price cannot exceed real price."
    assert err.value.details == "Received discounted price: 2.00; real price: 1.00."
