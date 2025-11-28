from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateRetailerRequest:
    retailer_uuid: UUID
    name: str
    url: str
    phone_number: str


@dataclass(frozen=True)
class CreateRetailerResponse:
    retailer_uuid: UUID
    name: str
