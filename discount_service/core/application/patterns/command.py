from typing import TypeVar


class Command:
    pass


GenericCommand = TypeVar("GenericCommand", bound=Command)
