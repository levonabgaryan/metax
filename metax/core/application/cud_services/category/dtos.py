import datetime as dt
from dataclasses import dataclass, field
from uuid import UUID

from metax.core.application.base_dtos.base_dtos import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class HelperWordPayloadRequestDTO:
    helper_word_text: str
    helper_word_uuid: UUID | None = None
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None


@dataclass(frozen=True)
class HelperWordPayloadResponseDTO:
    helper_word_text: str
    helper_word_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime


@dataclass(frozen=True)
class AddNewHelperWordsRequestDTO(RequestDTO):
    category_uuid: UUID
    new_helper_word_payload: HelperWordPayloadRequestDTO


@dataclass(frozen=True)
class AddNewHelperWordsResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    name: str
    new_helper_word_payload: HelperWordPayloadResponseDTO


@dataclass(frozen=True)
class CreateCategoryRequestDTO(RequestDTO):
    name: str
    helper_words_payload: list[HelperWordPayloadRequestDTO] = field(default_factory=list)


@dataclass(frozen=True)
class CreateCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    name: str
    helper_words_payload: list[HelperWordPayloadRequestDTO]


@dataclass(frozen=True)
class UpdateCategoryRequestDTO(RequestDTO):
    category_uuid: UUID
    new_name: str | None = None


@dataclass(frozen=True)
class UpdateCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    name: str
    helper_words_payload: list[HelperWordPayloadRequestDTO]


@dataclass(frozen=True)
class DeleteHelperWordRequestDTO(RequestDTO):
    category_uuid: UUID
    helper_word_uuid: UUID


@dataclass(frozen=True)
class DeleteCategoryRequestDTO(RequestDTO):
    category_uuid: UUID


@dataclass(frozen=True)
class DeleteCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID


@dataclass(frozen=True)
class DeleteHelperWordResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    name: str
    deleted_helper_word_payload: HelperWordPayloadResponseDTO


@dataclass(frozen=True)
class UpdateHelperWordTextRequestDTO(RequestDTO):
    category_uuid: UUID
    helper_word_uuid: UUID
    new_text: str


@dataclass(frozen=True)
class UpdateHelperWordTextResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    name: str
    helper_words_payload: HelperWordPayloadResponseDTO
