from decimal import Decimal

from app.main_error import MainError


class NegativePriceError(MainError):
    def __init__(self, incorrect_price: Decimal) -> None:
        super().__init__(
            message=f"Price {incorrect_price} cannot be negative.",
        )


class DiscountExceedsRealPriceError(MainError):
    def __init__(self, discounted_price: Decimal, real_price: Decimal) -> None:
        super().__init__(
            message=(
                f"Discounted price ({discounted_price}) "
                f"cannot exceed the real price ({real_price})."
            ),
        )
