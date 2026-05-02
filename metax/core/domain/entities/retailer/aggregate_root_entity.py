from __future__ import annotations

from datetime import datetime
from uuid import UUID

from metax.core.domain.ddd_patterns.aggregate import AggregateRootEntity
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject

from .value_objects import RetailersNames


class Retailer(AggregateRootEntity):
    def __init__(
        self,
        uuid_: UUID,
        created_at: datetime,
        updated_at: datetime,
        name: str,
        home_page_url: str,
        phone_number: str,
    ) -> None:
        super().__init__(
            uuid_value_object=UUIDValueObject.create(uuid_),
            datetime_details=EntityDateTimeDetails.create(
                created_at=created_at,
                updated_at=updated_at,
            ),
        )
        self.__name = RetailersNames(name)
        self.__home_page_url = home_page_url
        self.__phone_number = phone_number

    def get_home_page_url(self) -> str:
        return self.__home_page_url

    def get_name(self) -> str:
        return str(self.__name)

    def get_phone_number(self) -> str:
        return self.__phone_number

    def set_home_page_url(self, new_url: str) -> None:
        self.__home_page_url = new_url
        self._touch()

    def set_name(self, new_name: str) -> None:
        self.__name = RetailersNames(new_name)
        self._touch()

    def set_phone_number(self, new_phone_number: str) -> None:
        self.__phone_number = new_phone_number
        self._touch()
