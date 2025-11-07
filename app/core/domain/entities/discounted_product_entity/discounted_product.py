from dataclasses import dataclass
from uuid import UUID
from decimal import Decimal

from app.core.domain.ddd_patterns import AggregateRootEntity, ValueObject
from app.core.domain.entities.discounted_product_entity.exceptions import NegativePriceError, DiscountExceedsRealPriceError


class DiscountedProduct(AggregateRootEntity):
    def __init__(
        self,
        uuid_: UUID,
        category_uuid: UUID,
        retailer_uuid: UUID,
        price_details: PriceDetails,
        url: str,
    ) -> None:
        super().__init__(_uuid=uuid_)
        self.__category_uuid = category_uuid
        self.__retailer_uuid = retailer_uuid
        self.__price_details = price_details
        self.__url = url

    def get_url(self) -> str:
        return self.__url

    def get_category_uuid(self) -> UUID:
        return self.__category_uuid

    def get_retailer_uuid(self) -> UUID:
        return self.__retailer_uuid



@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class PriceDetails(ValueObject):
    real_price: Decimal
    discounted_price: Decimal

    def __post_init__(self) -> None:
        self.__validate_real_price()
        self.__validate_discounted_price()
        self.__validate_discount_is_less_than_real()

    def __validate_real_price(self) -> None:
        if self.real_price < Decimal('0.00'):
            raise NegativePriceError(incorrect_price=self.real_price)

    def __validate_discounted_price(self) -> None:
        if self.discounted_price < Decimal('0.00'):
            raise NegativePriceError(incorrect_price=self.discounted_price)

    def __validate_discount_is_less_than_real(self) -> None:
        if not self.discounted_price < self.real_price:
            raise DiscountExceedsRealPriceError(
                discounted_price=self.discounted_price,
                real_price=self.real_price
            )
