from __future__ import annotations

from datetime import datetime
from typing import Final, override
from uuid import UUID

from .general_value_objects import EntityDateTimeDetails, UUIDValueObject


class Entity:
    """Base Entity class.

    Entities are defined by a unique identifier (UUID) that establishes their
    identity and equality across the system.

    Note:
        Use public methods from Entity only in AggregateRootEntity.
        But if public methods are only for reading, you can use those everywhere (e.g. getters).
    """

    def __init__(self, uuid_value_object: UUIDValueObject, datetime_details: EntityDateTimeDetails) -> None:
        self._uuid_value_object: Final[UUIDValueObject] = uuid_value_object
        self._datetime_details = datetime_details

    def get_uuid(self) -> UUID:
        return self._uuid_value_object.value

    def get_created_at(self) -> datetime:
        return self._datetime_details.created_at

    def get_updated_at(self) -> datetime:
        return self._datetime_details.updated_at

    def _touch(self) -> None:
        self._datetime_details = self._datetime_details.renew_update_at(self._datetime_details)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._uuid_value_object.value == other._uuid_value_object.value

    @override
    def __hash__(self) -> int:
        """Generates a hash based on the entity's ID.

        The UUID ensures the same entity keeps the same identity for its lifecycle
        and supports constraints (e.g. no two different entities with the same logical ID).

        Returns:
            Hash of the entity UUID.
        """
        return hash(self._uuid_value_object.value)
