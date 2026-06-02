import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from metax.core.application.base_dtos.base_dtos import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class CreateCategoryRequestDTO(RequestDTO):
    name: str
    name_hy: str = ""
    name_ru: str = ""


@dataclass(frozen=True)
class CreateCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    name: str
    name_hy: str
    name_ru: str


@dataclass(frozen=True)
class UpdateCategoryRequestDTO(RequestDTO):
    category_uuid: UUID
    new_name: str | None = None
    new_name_hy: str | None = None
    new_name_ru: str | None = None


@dataclass(frozen=True)
class UpdateCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    name: str
    name_hy: str
    name_ru: str


@dataclass(frozen=True)
class DeleteCategoryRequestDTO(RequestDTO):
    category_uuid: UUID


@dataclass(frozen=True)
class DeleteCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID
