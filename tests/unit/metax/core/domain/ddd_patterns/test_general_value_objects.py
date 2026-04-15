from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from metax.core.domain.ddd_patterns.general_value_objects import (
    EntityDateTimeDetails,
    InvalidUtcDateTimeError,
    InvalidUUIDError,
    UpdateBeforeCreationError,
    UUIDValueObject,
)


def test_uuid_value_object_create_returns_uuid_v7() -> None:
    # when
    uuid_vo = UUIDValueObject.create()

    # then
    assert uuid_vo.value.version == 7


def test_uuid_value_object_raises_for_non_v7_uuid() -> None:
    # expect
    with pytest.raises(InvalidUUIDError):
        UUIDValueObject.create(value=uuid4())


def test_entity_datetime_details_raises_for_non_utc_datetime() -> None:
    # given
    naive_dt = datetime(2026, 1, 1)  # noqa: DTZ001

    # expect
    with pytest.raises(InvalidUtcDateTimeError):
        EntityDateTimeDetails.create(created_at=naive_dt, updated_at=naive_dt)


def test_entity_datetime_details_raises_when_updated_before_created() -> None:
    # given
    now = datetime.now(tz=timezone.utc)

    # expect
    with pytest.raises(UpdateBeforeCreationError):
        EntityDateTimeDetails.create(created_at=now, updated_at=now - timedelta(seconds=1))


def test_entity_datetime_details_renew_update_at_keeps_creation_date() -> None:
    # given
    details = EntityDateTimeDetails.create()

    # when
    renewed = EntityDateTimeDetails.renew_update_at(details)

    # then
    assert renewed.created_at == details.created_at
    assert renewed.updated_at >= details.updated_at
