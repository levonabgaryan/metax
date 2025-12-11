from typing import TypeVar


class DomainEvent:
    pass


GenericDomainEvent = TypeVar("GenericDomainEvent", bound=DomainEvent)
