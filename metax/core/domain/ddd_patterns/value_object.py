from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Self


class ValueObject(ABC):
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

    @classmethod
    @abstractmethod
    def create(cls, *args: Any, **kwargs: Any) -> Self:
        pass
