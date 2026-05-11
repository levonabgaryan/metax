import datetime as dt
from dataclasses import dataclass, field
from typing import Annotated
from uuid import UUID

from metax.core.application.base_dtos.base_dtos import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class CreateRetailerRequestDTO(RequestDTO):
    name: str
    home_page_url: str
    phone_number: str


@dataclass(frozen=True)
class CreateRetailerResponseDTO(ResponseDTO):
    retailer_uuid: UUID
    name: str
    phone_number: str
    home_page_url: str
    created_at: dt.datetime
    updated_at: dt.datetime


@dataclass(frozen=True)
class UpdateRetailerRequestDTO(RequestDTO):
    retailer_uuid: UUID
    new_name: Annotated[str | None, field(default=None)]
    new_home_page_url: Annotated[str | None, field(default=None)]
    new_phone_number: Annotated[str | None, field(default=None)]


@dataclass(frozen=True)
class UpdateRetailerResponseDTO(ResponseDTO):
    retailer_uuid: UUID
    new_name: str
    new_home_page_url: str
    new_phone_number: str
    created_at: dt.datetime
    updated_at: dt.datetime


@dataclass(frozen=True)
class DeleteRetailerRequestDTO(RequestDTO):
    retailer_uuid: UUID


@dataclass(frozen=True)
class DeleteRetailerResponseDTO(ResponseDTO):
    retailer_uuid: UUID
