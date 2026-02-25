from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.patterns.event import Event


@dataclass(frozen=True)
class RetailerUpdated(Event):
    retailer_uuid: UUID
