from uuid import uuid7

from metax.core.domain.entities.retailer.entity import Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def test_retailer_update() -> None:
    # given
    retailer = Retailer(
        retailer_uuid=uuid7(),
        name=RetailersNames.YEREVAN_CITY,
        home_page_url="test_url",
        phone_number="test_number",
    )

    # when
    retailer.set_name(RetailersNames.SAS_AM)
    retailer.set_home_page_url("new_url")
    retailer.set_phone_number("new_phone_number")

    # then
    assert retailer.get_name() == RetailersNames.SAS_AM
    assert retailer.get_home_page_url() == "new_url"
    assert retailer.get_phone_number() == "new_phone_number"
