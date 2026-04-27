from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from metax.core.application.base_dtos.base_dtos import RequestDTO, ResponseDTO


@dataclass(frozen=True)
class HelperWordPayload:
    text: str
    helper_word_uuid: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class AddNewHelperWordsRequestDTO(RequestDTO):
    category_uuid: UUID
    new_helper_words_payload: list[HelperWordPayload]


@dataclass(frozen=True)
class AddNewHelperWordsResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    new_helper_words_payload: list[HelperWordPayload]


@dataclass(frozen=True)
class CreateCategoryRequestDTO(RequestDTO):
    name: str
    helper_words_payload: list[HelperWordPayload] = field(default_factory=list)


@dataclass(frozen=True)
class CreateCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    helper_words_payload: list[HelperWordPayload]


@dataclass(frozen=True)
class UpdateCategoryRequestDTO(RequestDTO):
    category_uuid: UUID
    new_name: str | None = None


@dataclass(frozen=True)
class UpdateCategoryResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    helper_words_payload: list[HelperWordPayload]


@dataclass(frozen=True)
class DeleteHelperWordsRequestDTO(RequestDTO):
    category_uuid: UUID
    helper_words_uuid: list[UUID]


@dataclass(frozen=True)
class DeleteHelperWordsResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    helper_words_payload: list[HelperWordPayload]


@dataclass(frozen=True)
class UpdateHelperWordTextRequestDTO(RequestDTO):
    category_uuid: UUID
    helper_word_uuid: UUID
    new_text: str


@dataclass(frozen=True)
class UpdateHelperWordTextResponseDTO(ResponseDTO):
    category_uuid: UUID
    created_at: datetime
    updated_at: datetime
    name: str
    helper_words_payload: list[HelperWordPayload]
