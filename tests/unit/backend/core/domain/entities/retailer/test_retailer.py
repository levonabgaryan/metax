from uuid import uuid4

from backend.core.domain.entities.retailer_entity.retailer import Retailer


def test_retailer_update() -> None:
    # given
    retailer = Retailer(retailer_uuid=uuid4(), name="test_name", url="test_url", phone_number="test_number")

    new_data = {
        "retailer_name": "new_name",
        "retailer_url": "new_url",
        "retailer_phone_number": "new_phone_number",
    }

    # when
    retailer.update(new_data)

    # then
    assert retailer.get_name() == new_data["retailer_name"]
    assert retailer.get_url() == new_data["retailer_url"]
    assert retailer.get_phone_number() == new_data["retailer_phone_number"]
