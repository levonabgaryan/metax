from decimal import Decimal

from backend.main_error import MainError

from .error_codes import DiscountedProductErrorCodes


class NegativePriceError(MainError):
    def __init__(self, incorrect_price: Decimal) -> None:
        msg = f"Price {incorrect_price} cannot be negative."
        super().__init__(message=msg, error_code=DiscountedProductErrorCodes.NEGATIVE_PRICE)


class DiscountExceedsRealPriceError(MainError):
    def __init__(self, discounted_price: Decimal, real_price: Decimal) -> None:
        msg = f"Discounted price ({discounted_price}) cannot exceed the real price ({real_price})."
        super().__init__(message=msg, error_code=DiscountedProductErrorCodes.DISCOUNT_EXCEEDS_PRICE)
