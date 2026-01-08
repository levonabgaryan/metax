from collections import deque
from typing import Final, override
from uuid import UUID

from discount_service.core.domain.event import Event


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

    def __init__(self, _uuid: UUID) -> None:
        super().__init__(_uuid)
        self._events: deque[Event] = deque()

    @property
    def has_events(self) -> bool:
        return len(self._events) > 0

    def get_one_event(self) -> Event:
        return self._events.popleft()

    def _record_event(self, event: Event) -> None:
        self._events.append(event)

    def pull_events(self) -> list[Event]:
        # Helper method: take all events packed in list and clear dequeue
        events = list(self._events)
        self._events.clear()
        return events
