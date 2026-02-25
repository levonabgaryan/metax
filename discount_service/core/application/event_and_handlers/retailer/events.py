from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from discount_service.core.application.patterns.message_bus_1 import Event


@dataclass(frozen=True)
class RetailerUpdated(Event):
    retailer_uuid: UUID
