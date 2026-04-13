from __future__ import annotations

from datetime import datetime
from typing import Final, override
from uuid import UUID

from .general_value_objects import EntityDateTimeDetails, UUIDValueObject


class Entity:
    """Base Entity class.

    Entities are defined by a unique identifier (UUID) that establishes their
    identity and equality across the system.
    """

    def __init__(self, uuid_value_object: UUIDValueObject, datetime_details: EntityDateTimeDetails) -> None:
        self.__uuid_value_object: Final[UUIDValueObject] = uuid_value_object
        self.__datetime_details = datetime_details

    def get_uuid(self) -> UUID:
        return self.__uuid_value_object.value

    def get_created_at(self) -> datetime:
        return self.__datetime_details.created_at

    def get_updated_at(self) -> datetime:
        return self.__datetime_details.updated_at

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.get_uuid() == other.get_uuid()

    @override
    def __hash__(self) -> int:
        """Generates a hash based on the entity's ID.

        The UUID ensures the same entity keeps the same identity for its lifecycle
        and supports constraints (e.g. no two different entities with the same logical ID).
        """
        return hash(self.get_uuid())


class AggregateRootEntity(Entity):
    """Base aggregate root entity class.

    All aggregate root entities should inherit from this class.
    It inherits from the Entity class because an AggregateRootEntity is also an entity.
    This makes the design clearer.
    """

    def __init__(self, uuid_value_object: UUIDValueObject, datetime_details: EntityDateTimeDetails) -> None:
        super().__init__(uuid_value_object=uuid_value_object, datetime_details=datetime_details)


class ValueObject:
    """Base class for Value Objects (VOs).

    Inherited classes should be decorated with
    `@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)`.
    Or should be an Enum object.

    Example:
        >>> @dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
        ... class SomeVO(ValueObject):
        ...     name: str

    Note:
        Value Objects define identity based on their attributes, are immutable,
        and have no lifecycle.
        Always implement a 'create' method for every value object, and use that method for creating a value object.
    """
