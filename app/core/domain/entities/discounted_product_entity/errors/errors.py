from decimal import Decimal

from app.core.domain.domain_error import DomainError


class NegativePriceError(DomainError):
    def __init__(self, incorrect_price: Decimal) -> None:
        super().__init__(
            message=f"Price {incorrect_price} cannot be negative.",
        )


class DiscountExceedsRealPriceError(DomainError):
    def __init__(self, discounted_price: Decimal, real_price: Decimal) -> None:
        super().__init__(
            message=f"Discounted price ({discounted_price}) cannot exceed the real price ({real_price}).",
        )
