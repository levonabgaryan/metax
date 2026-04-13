from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Self, override
from uuid import UUID

from metax_main_error import MetaxError

from .ddd_patterns import ValueObject


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class UUIDValueObject(ValueObject):
    value: UUID

    def __post_init__(self) -> None:
        self.__validate_uuid()

    @override
    @classmethod
    def create(cls, value: UUID | None = None) -> Self:
        value = value or uuid.uuid7()
        return cls(value)

    def __validate_uuid(self) -> None:
        try:
            UUID(str(self.value))
        except ValueError as err:
            raise InvalidUUIDError(self.value) from err

        if self.value.version != 7:
            raise InvalidUUIDError(uuid_=self.value)


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class EntityDateTimeDetails(ValueObject):
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        self.__validate_utc(self.created_at)
        self.__validate_utc(self.updated_at)
        self.__validate_update_is_after_creation()

    @override
    @classmethod
    def create(cls, created_at: datetime | None = None, updated_at: datetime | None = None) -> Self:
        created = created_at or datetime.now(tz=timezone.utc)
        updated = updated_at or datetime.now(tz=timezone.utc)
        return cls(created_at=created, updated_at=updated)

    @classmethod
    def renew_update_at(cls, old: Self) -> Self:
        return cls.create(created_at=old.created_at, updated_at=datetime.now(tz=timezone.utc))

    @staticmethod
    def __validate_utc(dt: datetime) -> None:
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise InvalidUtcDateTimeError
        if dt.tzinfo != timezone.utc:
            raise InvalidUtcDateTimeError

    def __validate_update_is_after_creation(self) -> None:
        if self.created_at > self.updated_at:
            raise UpdateBeforeCreationError


class InvalidUUIDError(MetaxError):
    def __init__(self, uuid_: UUID) -> None:
        super().__init__(
            error_code="INVALID_UUID", title=f"Invalid uuid format: {uuid_}", details="UUID should be of version 7"
        )


class InvalidUtcDateTimeError(MetaxError):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            error_code="DATETIME_NOT_UTC",
            title="The datetime object must be in UTC format",
            details="Native date times or local timezones are not allowed. Use datetime.now(timezone.utc).",
        )


class UpdateBeforeCreationError(MetaxError):
    def __init__(self) -> None:
        super().__init__(
            error_code="UPDATE_BEFORE_CREATION",
            title="The update date cannot be earlier than the creation date.",
            details="The chronological order invariant was violated:"
            " the timestamp value 'updated_at' must be greater than or equal to 'created_at'.",
        )
