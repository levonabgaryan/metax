from uuid import uuid4

from discount_service.core.domain.entities.retailer_entity.retailer import Retailer, DataForRetailerUpdate


def test_retailer_update() -> None:
    # given
    retailer = Retailer(retailer_uuid=uuid4(), name="test_name", url="test_url", phone_number="test_number")

    new_data = DataForRetailerUpdate(
        new_name="new_name",
        new_url="new_url",
        new_phone_number="new_phone_number",
    )

    # when
    retailer.update(new_data)

    # then
    assert retailer.get_name() == new_data["new_name"]
    assert retailer.get_url() == new_data["new_url"]
    assert retailer.get_phone_number() == new_data["new_phone_number"]
