from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.domain.ddd_patterns import AggregateRootEntity, ValueObject


class Category(AggregateRootEntity):
    def __init__(
        self,
        category_uuid: UUID,
        name: str,
        helper_words: CategoryHelperWords,
    ) -> None:
        super().__init__(_uuid=category_uuid)
        self.__name = name
        self.__helper_words = helper_words


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class CategoryHelperWords(ValueObject):
    words: frozenset[str]
