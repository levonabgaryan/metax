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
        examples: list[str] | None = None,
        keywords: list[str] | None = None,
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
        # Example product names that belong to this category; used as extra match anchors by the
        # embedding classifier so a product like "կարագ" lands in the right category.
        self.__examples = examples or []
        # Exact keyword phrases that assign a product to this category outright (whole-word match on
        # the product's noun phrase). Higher priority and stricter than the embedding examples.
        self.__keywords = keywords or []

    def get_keywords(self) -> list[str]:
        return self.__keywords

    def set_keywords(self, new_keywords: list[str]) -> None:
        self.__keywords = new_keywords
        self._touch()

    def get_examples(self) -> list[str]:
        return self.__examples

    def set_examples(self, new_examples: list[str]) -> None:
        self.__examples = new_examples
        self._touch()

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
