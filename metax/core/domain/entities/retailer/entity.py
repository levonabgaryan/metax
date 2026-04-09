from __future__ import annotations
from typing import TypedDict
from uuid import UUID

from metax.core.domain.ddd_patterns import AggregateRootEntity
from .value_objects import RetailersNames


class Retailer(AggregateRootEntity):
    def __init__(
        self,
        retailer_uuid: UUID,
        name: RetailersNames,
        home_page_url: str,
        phone_number: str,
    ) -> None:
        super().__init__(uuid_=retailer_uuid)
        self.__name = name
        self.__home_page_url = home_page_url
        self.__phone_number = phone_number

    def set_name(self, new_name: RetailersNames) -> None:
        self.__name = new_name

    def set_home_page_url(self, new_url: str) -> None:
        self.__home_page_url = new_url

    def set_phone_number(self, new_phone_number: str) -> None:
        self.__phone_number = new_phone_number

    def get_name(self) -> RetailersNames:
        return self.__name

    def get_home_page_url(self) -> str:
        return self.__home_page_url

    def get_phone_number(self) -> str:
        return self.__phone_number

    def update(self, new_data: DataForRetailerUpdate) -> None:
        if "new_name" in new_data:
            new_name = new_data["new_name"]
            if new_name is not None:
                self.set_name(RetailersNames(new_name))
        if "new_url" in new_data:
            new_url = new_data["new_url"]
            if new_url is not None:
                self.set_home_page_url(new_url)
        if "new_phone_number" in new_data:
            new_phone = new_data["new_phone_number"]
            if new_phone is not None:
                self.set_phone_number(new_phone)


class DataForRetailerUpdate(TypedDict, total=False):
    new_name: str | None
    new_url: str | None
    new_phone_number: str | None
