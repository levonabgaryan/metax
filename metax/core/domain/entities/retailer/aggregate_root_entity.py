from __future__ import annotations

import datetime as dt
from uuid import UUID

from metax.core.domain.ddd_patterns.aggregate import AggregateRootEntity
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject

from .value_objects import parse_retailer_name


class Retailer(AggregateRootEntity):
    def __init__(
        self,
        uuid_: UUID,
        created_at: dt.datetime,
        updated_at: dt.datetime,
        name: str,
        home_page_url: str,
        phone_number: str,
        default_category_uuid: UUID | None = None,
    ) -> None:
        super().__init__(
            uuid_value_object=UUIDValueObject.create(uuid_),
            datetime_details=EntityDateTimeDetails.create(
                created_at=created_at,
                updated_at=updated_at,
            ),
        )
        self.__name = parse_retailer_name(name)
        self.__home_page_url = home_page_url
        self.__phone_number = phone_number
        # When set, every product this retailer sells is stamped with this category directly, and the
        # embedding classifier is skipped for it — for retailers whose whole catalog is one category.
        self.__default_category_uuid = default_category_uuid

    def get_default_category_uuid(self) -> UUID | None:
        return self.__default_category_uuid

    def get_home_page_url(self) -> str:
        return self.__home_page_url

    def get_name(self) -> str:
        return str(self.__name)

    def get_phone_number(self) -> str:
        return self.__phone_number

    def set_default_category_uuid(self, new_default_category_uuid: UUID | None) -> None:
        self.__default_category_uuid = new_default_category_uuid
        self._touch()

    def set_home_page_url(self, new_url: str) -> None:
        self.__home_page_url = new_url
        self._touch()

    def set_name(self, new_name: str) -> None:
        self.__name = parse_retailer_name(new_name)
        self._touch()

    def set_phone_number(self, new_phone_number: str) -> None:
        self.__phone_number = new_phone_number
        self._touch()
