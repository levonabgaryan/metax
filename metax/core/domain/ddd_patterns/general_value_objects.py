from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass
from typing import Self, override
from uuid import UUID

from constants import ErrorCodes
from metax_error import MetaxError

from .value_object import ValueObject


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class UUIDValueObject(ValueObject):
    value: UUID

    def __post_init__(self) -> None:
        self.__validate_uuid()

    @override
    @classmethod
    def create(cls, value: UUID | None = None) -> Self:
        if value is None:
            return cls(uuid.uuid7())
        return cls(value=value)

    def __validate_uuid(self) -> None:
        try:
            UUID(str(self.value))
        except ValueError as err:
            raise InvalidUUIDError(self.value) from err

        if self.value.version != 7:
            raise InvalidUUIDError(uuid_=self.value)


@dataclass(frozen=True, unsafe_hash=False, eq=True, slots=True)
class EntityDateTimeDetails(ValueObject):
    created_at: dt.datetime
    updated_at: dt.datetime

    def __post_init__(self) -> None:
        self.__validate_utc(self.created_at)
        self.__validate_utc(self.updated_at)
        self.__validate_update_is_after_creation()

    @override
    @classmethod
    def create(cls, created_at: dt.datetime | None = None, updated_at: dt.datetime | None = None) -> Self:
        created = created_at or dt.datetime.now(tz=dt.UTC)
        updated = updated_at or dt.datetime.now(tz=dt.UTC)
        return cls(created_at=created, updated_at=updated)

    @classmethod
    def renew_update_at(cls, old: Self) -> Self:
        return cls.create(created_at=old.created_at, updated_at=dt.datetime.now(tz=dt.UTC))

    def __validate_update_is_after_creation(self) -> None:
        if self.created_at > self.updated_at:
            raise UpdateBeforeCreationError

    @staticmethod
    def __validate_utc(value: dt.datetime) -> None:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise InvalidUtcDateTimeError
        if value.tzinfo != dt.UTC:
            raise InvalidUtcDateTimeError


class InvalidUUIDError(MetaxError):
    def __init__(self, uuid_: UUID) -> None:
        super().__init__(
            error_code=ErrorCodes.INVALID_UUID,
            title="Invalid UUID format.",
            details=f"Received value: {uuid_}. Expected UUID version 7.",
        )


class InvalidUtcDateTimeError(MetaxError):
    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCodes.DATETIME_NOT_UTC,
            title="Datetime must be in UTC.",
            details="Naive datetimes and non-UTC timezones are not allowed. Use datetime.now(timezone.utc).",
        )


class UpdateBeforeCreationError(MetaxError):
    def __init__(self) -> None:
        super().__init__(
            error_code=ErrorCodes.UPDATE_BEFORE_CREATION,
            title="Update time cannot be earlier than creation time.",
            details="Invariant violated: 'updated_at' must be greater than or equal to 'created_at'.",
        )
