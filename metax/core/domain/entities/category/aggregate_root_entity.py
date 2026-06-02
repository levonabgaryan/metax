from __future__ import annotations

import datetime as dt
from uuid import UUID

from metax.core.domain.ddd_patterns import AggregateRootEntity
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject


class Category(AggregateRootEntity):
    def __init__(
        self,
        uuid_: UUID,
        created_at: dt.datetime,
        updated_at: dt.datetime,
        name: str,
        name_hy: str = "",
        name_ru: str = "",
    ) -> None:
        super().__init__(
            uuid_value_object=UUIDValueObject.create(uuid_),
            datetime_details=EntityDateTimeDetails.create(
                created_at=created_at,
                updated_at=updated_at,
            ),
        )
        self.__name = name
        self.__name_hy = name_hy
        self.__name_ru = name_ru

    def get_name(self) -> str:
        return self.__name

    def get_name_hy(self) -> str:
        return self.__name_hy

    def get_name_ru(self) -> str:
        return self.__name_ru

    def set_name(self, new_name: str) -> None:
        self.__name = new_name
        self._touch()

    def set_name_hy(self, new_name_hy: str) -> None:
        self.__name_hy = new_name_hy
        self._touch()

    def set_name_ru(self, new_name_ru: str) -> None:
        self.__name_ru = new_name_ru
        self._touch()
