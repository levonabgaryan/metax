from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated
from uuid import UUID

from metax.core.application.base_dtos.base_dtos import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class CreateRetailerRequestDTO(RequestDTO):
    name: str
    url: str
    phone_number: str


@dataclass(frozen=True)
class CreateRetailerResponseDTO(ResponseDTO):
    retailer_uuid: UUID
    name: str
    phone_number: str
    home_page_url: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UpdateRetailerRequestDTO(RequestDTO):
    retailer_uuid: UUID
    new_name: Annotated[str | None, field(default=None)]
    new_url: Annotated[str | None, field(default=None)]
    new_phone_number: Annotated[str | None, field(default=None)]


@dataclass(frozen=True)
class UpdateRetailerResponseDTO(ResponseDTO):
    retailer_uuid: UUID
    new_name: str
    new_url: str
    new_phone_number: str
    created_at: datetime
    updated_at: datetime
