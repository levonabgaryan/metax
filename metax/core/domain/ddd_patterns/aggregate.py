from __future__ import annotations

from .entity import Entity
from .general_value_objects import EntityDateTimeDetails, UUIDValueObject


class AggregateRootEntity(Entity):
    """Base aggregate root entity class.

    All aggregate root entities should inherit from this class.
    It inherits from the Entity class because an AggregateRootEntity is also an entity.
    This makes the design clearer.
    """

    def __init__(self, uuid_value_object: UUIDValueObject, datetime_details: EntityDateTimeDetails) -> None:
        super().__init__(uuid_value_object=uuid_value_object, datetime_details=datetime_details)
