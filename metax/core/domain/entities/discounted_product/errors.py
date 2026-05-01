from decimal import Decimal

from constants import ErrorCodes
from metax_main_error import MetaxError


class NegativePriceError(MetaxError):
    def __init__(self, value: Decimal) -> None:
        title = "Price cannot be negative."
        details = f"Received value: {value}."
        super().__init__(title=title, error_code=ErrorCodes.NEGATIVE_PRICE, details=details)


class DiscountExceedsRealPriceError(MetaxError):
    def __init__(self, discounted_price: Decimal, real_price: Decimal) -> None:
        title = "Discounted price cannot exceed real price."
        details = f"Received discounted price: {discounted_price}; real price: {real_price}."
        super().__init__(title=title, error_code=ErrorCodes.DISCOUNT_EXCEEDS_PRICE, details=details)
