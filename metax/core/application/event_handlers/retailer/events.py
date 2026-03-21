from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from metax.core.application.event_handlers.event import Event


@dataclass(frozen=True)
class RetailerUpdated(Event):
    retailer_uuid: UUID
