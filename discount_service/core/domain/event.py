from typing import TypeVar


class Event:
    pass


GenericEvent = TypeVar("GenericEvent", bound=Event)
