from uuid import uuid4

from metax.core.domain.entities.retailer.entity import DataForRetailerUpdate, Retailer
from metax.core.domain.entities.retailer.value_objects import RetailersNames


def test_retailer_update() -> None:
    # given
    retailer = Retailer(
        retailer_uuid=uuid4(),
        name=RetailersNames.YEREVAN_CITY,
        home_page_url="test_url",
        phone_number="test_number",
    )

    new_data = DataForRetailerUpdate(
        new_name=RetailersNames.SAS_AM.value,
        new_url="new_url",
        new_phone_number="new_phone_number",
    )

    # when
    retailer.update(new_data)

    # then
    assert retailer.get_name() == RetailersNames.SAS_AM
    assert retailer.get_home_page_url() == new_data["new_url"]
    assert retailer.get_phone_number() == new_data["new_phone_number"]
