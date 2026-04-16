from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from metax.core.domain.ddd_patterns import AggregateRootEntity
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject
from metax.core.domain.entities.discounted_product.value_objects import PriceDetails


class DiscountedProduct(AggregateRootEntity):
    def __init__(
        self,
        uuid_: UUIDValueObject,
        category_uuid: UUIDValueObject | None,
        retailer_uuid: UUIDValueObject,
        price_details: PriceDetails,
        datetime_details: EntityDateTimeDetails,
        name: str,
        url: str,
    ) -> None:
        super().__init__(uuid_value_object=uuid_, datetime_details=datetime_details)
        self.__category_uuid = category_uuid
        self.__retailer_uuid = retailer_uuid
        self.__price_details = price_details
        self.__name = name
        self.__url = url

    def get_url(self) -> str:
        return self.__url

    def set_url(self, url: str) -> None:
        self.__url = url
        self._touch()

    def get_name(self) -> str:
        return self.__name

    def set_name(self, name: str) -> None:
        self.__name = name
        self._touch()

    def get_real_price(self) -> Decimal:
        return self.__price_details.real_price

    def get_discounted_price(self) -> Decimal:
        return self.__price_details.discounted_price

    def has_category(self) -> bool:
        return self.__category_uuid is not None

    def get_category_uuid(self) -> UUID:
        if self.__category_uuid is None:
            msg = f"DiscountedProduct {self.get_uuid()} doesn't have a category assigned."
            raise AttributeError(msg)
        return self.__category_uuid.value

    def set_category_uuid(self, category_uuid: UUIDValueObject | None) -> None:
        self.__category_uuid = category_uuid
        self._touch()

    def get_retailer_uuid(self) -> UUID:
        return self.__retailer_uuid.value
