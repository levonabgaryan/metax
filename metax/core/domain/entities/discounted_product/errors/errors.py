from decimal import Decimal

from metax_main_error import MetaxError

from .error_codes import DiscountedProductErrorCodes


class NegativePriceError(MetaxError):
    def __init__(self, price_type: str, incorrect_price: Decimal) -> None:
        msg = f"{price_type} cannot be negative."
        details = {"price_type": price_type, "incorrect_price": str(incorrect_price)}
        super().__init__(title=msg, error_code=DiscountedProductErrorCodes.NEGATIVE_PRICE, details=details)


class DiscountExceedsRealPriceError(MetaxError):
    def __init__(self, discounted_price: Decimal, real_price: Decimal) -> None:
        msg = f"Discounted price ({discounted_price}) cannot exceed the real price ({real_price})."
        super().__init__(title=msg, error_code=DiscountedProductErrorCodes.DISCOUNT_EXCEEDS_PRICE)
