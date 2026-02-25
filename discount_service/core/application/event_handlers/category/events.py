from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.patterns.event import Event


@dataclass(frozen=True)
class CategoryUpdated(Event):
    category_uuid: UUID
