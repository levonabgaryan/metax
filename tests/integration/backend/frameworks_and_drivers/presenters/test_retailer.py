from typing import Any
from uuid import uuid4

import pytest

from backend.core.application.patterns.use_case_abc import EmptyResponseDTO
from backend.core.application.use_cases.retailer.dtos import RetailerEntityResponseDTO
from backend.frameworks_and_drivers.di.presenters_container import PresentersContainer
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel


@pytest.mark.parametrize("dto", [EmptyResponseDTO(), None])
def test_present_empty_view_model(presenters_container: PresentersContainer, dto: Any) -> None:
    # given
    presenter = presenters_container.retailer_presenter()

    # when
    view_model: EmptyViewModel = presenter.present(dto)

    # then
    assert isinstance(view_model, dict)
    assert not view_model


def test_present_retailer_response_dto(presenters_container: PresentersContainer) -> None:
    # given
    presenter = presenters_container.retailer_presenter()
    dto = RetailerEntityResponseDTO(
        retailer_uuid=uuid4(),
        name="test_retailer_name",
        url="test_retailer_url",
        phone_number="test_retailer_number",
    )

    # when
    view_model = presenter.present(dto)

    # then
    assert isinstance(view_model, dict)
    assert view_model["retailer_uuid"] == str(dto.retailer_uuid)
    assert view_model["name"] == dto.name
    assert view_model["url"] == dto.url
    assert view_model["phone_number"] == dto.phone_number
