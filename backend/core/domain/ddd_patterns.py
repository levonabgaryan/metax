from typing import Final, override
from uuid import UUID

from backend.core.domain.event import Event


class ValueObject:
    """
    Base class for Value Objects (VOs).

    Inherited classes should be decorated with
    `@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)`.

    Example:
        >>> @dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
        ... class SomeVO(ValueObject):
        ...     name: str

    Value Objects define identity based on their attributes, are immutable,
    and have no lifecycle.
    """


class Entity:
    """
    Base Entity class.

    Entities are defined by a unique identifier (UUID) that establishes their
    identity and equality across the system.
    """

    def __init__(self, _uuid: UUID) -> None:
        self._uuid: Final[UUID] = _uuid

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._uuid == other._uuid

    @override
    def __hash__(self) -> int:
        """
        Generates a hash based on the entity's ID.

        Since '_uuid' is a UUID, the system ensures that the same entity will always
        have the same ID throughout its lifecycle. This unique identity is used to
        ensure database constraints (e.g., preventing the saving of two different
        entities with the same logical ID).
        """
        return hash(self._uuid)

    def get_uuid(self) -> UUID:
        return self._uuid


class AggregateRootEntity(Entity):
    """
    Base aggregate root entity class.

    All aggregate root entities should inherit from this class.
    It inherits from the Entity class because an AggregateRootEntity is also an entity.
    This makes the design clearer.
    """

    @property
    def has_events(self) -> bool:
        raise NotImplementedError

    def get_one_event(self) -> Event:
        raise NotImplementedError
