from dataclasses import dataclass, field
from uuid import UUID


from backend.core.application.patterns.use_case_abc import ResponseDTO


@dataclass(frozen=True)
class RetailerEntityResponseDTO(ResponseDTO):
    retailer_uuid: UUID
    name: str
    url: str | None = field(default=None)
    phone_number: str | None = field(default=None)
