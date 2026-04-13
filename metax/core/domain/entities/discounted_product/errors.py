from decimal import Decimal

from metax_main_error import MetaxError


class NegativePriceError(MetaxError):
    def __init__(self, value: Decimal) -> None:
        msg = f"{value} cannot be negative."
        super().__init__(title=msg, error_code="NEGATIVE_PRICE")


class DiscountExceedsRealPriceError(MetaxError):
    def __init__(self, discounted_price: Decimal, real_price: Decimal) -> None:
        msg = f"Discounted price ({discounted_price}) cannot exceed the real price ({real_price})."
        super().__init__(title=msg, error_code="DISCOUNT_EXCEEDS_PRICE")
