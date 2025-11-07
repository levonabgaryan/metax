from decimal import Decimal

from app.main_exception import MainException


class NegativePriceError(MainException):
    def __init__(self, incorrect_price: Decimal) -> None:
        super().__init__(
            message=f"Price {incorrect_price} cannot be negative."
        )


class DiscountExceedsRealPriceError(MainException):
    def __init__(self, discounted_price: Decimal, real_price: Decimal) -> None:
        super().__init__(
            message=(
                f"Discounted price ({discounted_price}) cannot exceed "
                f"the real price ({real_price})."
            )
        )
