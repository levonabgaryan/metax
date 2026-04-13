from datetime import datetime, timezone
from uuid import uuid7

from metax.core.domain.ddd_patterns.general_value_objects import EntityDateTimeDetails, UUIDValueObject
from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def test_retailer_update() -> None:
    # given
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    retailer = Retailer(
        retailer_uuid=UUIDValueObject.create(uuid7()),
        name=RetailersNames.YEREVAN_CITY,
        home_page_url="test_url",
        phone_number="test_number",
        datetime_details=EntityDateTimeDetails.create(created_at=ts, updated_at=ts),
    )

    # when
    retailer.set_name(RetailersNames.SAS_AM)
    retailer.set_home_page_url("new_url")
    retailer.set_phone_number("new_phone_number")

    # then
    assert retailer.get_name() == RetailersNames.SAS_AM
    assert retailer.get_home_page_url() == "new_url"
    assert retailer.get_phone_number() == "new_phone_number"
