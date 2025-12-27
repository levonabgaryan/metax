from dataclasses import dataclass
from uuid import UUID

from backend.core.domain.event import Event


@dataclass(frozen=True)
class CategoryNameUpdated(Event):
    category_uuid: UUID
    new_name: str
