from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.event_handlers.event import Event


@dataclass(frozen=True)
class CategoryUpdated(Event):
    category_uuid: UUID
