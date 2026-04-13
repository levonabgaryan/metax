from __future__ import annotations

from datetime import datetime
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
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(retailer_uuid, created_at, updated_at)
        self.__name = name
        self.__home_page_url = home_page_url
        self.__phone_number = phone_number

    def get_name(self) -> RetailersNames:
        return self.__name

    def set_name(self, new_name: RetailersNames) -> None:
        self.__name = new_name

    def set_home_page_url(self, new_url: str) -> None:
        self.__home_page_url = new_url

    def get_home_page_url(self) -> str:
        return self.__home_page_url

    def get_phone_number(self) -> str:
        return self.__phone_number

    def set_phone_number(self, new_phone_number: str) -> None:
        self.__phone_number = new_phone_number
