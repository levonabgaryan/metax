from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django_framework.metax.models import RetailerModel


@pytest.mark.django_db
def test_retailer_model_rejects_name_not_in_retailers_names() -> None:
    retailer = RetailerModel(
        retailer_uuid=uuid4(),
        name="unknown-retailer-slug",
        url="https://example.com/",
        phone_number="12345678",
    )

    with pytest.raises(ValidationError) as exc_info:
        retailer.full_clean()
        retailer.save()

    assert "name" in exc_info.value.error_dict
