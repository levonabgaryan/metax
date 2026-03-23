from typing import Final, override
from uuid import UUID


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

    def __init__(self, uuid: UUID) -> None:
        self.__uuid: Final[UUID] = uuid

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.get_uuid() == other.get_uuid()

    @override
    def __hash__(self) -> int:
        """
        Generates a hash based on the entity's ID.

        The UUID ensures the same entity keeps the same identity for its lifecycle
        and supports constraints (e.g. no two different entities with the same logical ID).
        """
        return hash(self.get_uuid())

    def get_uuid(self) -> UUID:
        return self.__uuid


class AggregateRootEntity(Entity):
    """
    Base aggregate root entity class.

    All aggregate root entities should inherit from this class.
    It inherits from the Entity class because an AggregateRootEntity is also an entity.
    This makes the design clearer.
    """

    def __init__(self, uuid: UUID) -> None:
        super().__init__(uuid)
