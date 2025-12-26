from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from backend.core.application.patterns.use_case_abc import EmptyResponseDTO
from backend.core.application.use_cases.discounted_product.dtos import DiscountedProductEntityResponseDTO
from backend.core.domain.entities.discounted_product_entity.discounted_product import PriceDetails
from backend.frameworks_and_drivers.di.presenters_container import PresentersContainer
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel


@pytest.mark.parametrize("dto", [EmptyResponseDTO(), None])
def test_present_empty_view_model(presenters_container: PresentersContainer, dto: Any) -> None:
    # given
    presenter = presenters_container.discounted_product_presenter()

    # when
    view_model: EmptyViewModel = presenter.present(dto)

    # then
    assert isinstance(view_model, dict)
    assert not view_model


def test_present_discounted_product_response_dto(presenters_container: PresentersContainer) -> None:
    # given
    presenter = presenters_container.discounted_product_presenter()
    dto = DiscountedProductEntityResponseDTO(
        discounted_product_uuid=uuid4(),
        retailer_name="test_retailer",
        name="test_name",
        price_details=PriceDetails(
            real_price=Decimal("100"),
            discounted_price=Decimal("50"),
        ),
        url="test_url",
        category_name="test_category",
    )

    # when
    view_model = presenter.present(dto)

    # then
    assert isinstance(view_model, dict)
    assert view_model["discounted_product_uuid"] == str(dto.discounted_product_uuid)
    assert view_model["retailer_name"] == dto.retailer_name
    assert view_model["name"] == dto.name
    assert view_model["real_price"] == str(dto.price_details.real_price)
    assert view_model["discounted_price"] == str(dto.price_details.discounted_price)
    assert view_model["url"] == dto.url
    assert view_model["category_name"] == dto.category_name
