from datetime import datetime
from uuid import UUID

from metax.core.domain.ddd_patterns import Entity
from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject


class CategoryHelperWord(Entity):
    def __init__(
        self,
        uuid_: UUID,
        created_at: datetime,
        updated_at: datetime,
        helper_word_text: str,
    ) -> None:
        super().__init__(
            uuid_value_object=UUIDValueObject.create(uuid_),
            datetime_details=EntityDateTimeDetails.create(
                created_at=created_at,
                updated_at=updated_at,
            ),
        )
        self.__helper_word_text = helper_word_text

    def get_helper_word_text(self) -> str:
        return self.__helper_word_text

    def set_helper_word_text(self, new_value: str) -> None:
        # Use this method only in AggregateRootEntity
        self.__helper_word_text = new_value
        self._touch()
