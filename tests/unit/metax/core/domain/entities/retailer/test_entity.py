from datetime import datetime, timezone
from uuid import uuid7

from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def test_retailer_update() -> None:
    # given
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    retailer = Retailer(
        uuid_=uuid7(),
        name=RetailersNames.YEREVAN_CITY,
        home_page_url="test_url",
        phone_number="test_number",
        created_at=ts,
        updated_at=ts,
    )

    # when
    retailer.set_name(RetailersNames.SAS_AM)
    retailer.set_home_page_url("new_url")
    retailer.set_phone_number("new_phone_number")

    # then
    assert retailer.get_name() == RetailersNames.SAS_AM
    assert retailer.get_home_page_url() == "new_url"
    assert retailer.get_phone_number() == "new_phone_number"


def test_retailer_setter_touches_updated_at() -> None:
    # given
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    retailer = Retailer(
        uuid_=uuid7(),
        created_at=ts,
        updated_at=ts,
        name=RetailersNames.YEREVAN_CITY,
        home_page_url="test_url",
        phone_number="test_number",
    )
    old_created_at = retailer.get_created_at()
    old_updated_at = retailer.get_updated_at()

    # when
    retailer.set_name(RetailersNames.SAS_AM)

    # then
    assert retailer.get_created_at() == old_created_at
    assert retailer.get_updated_at() >= old_updated_at
