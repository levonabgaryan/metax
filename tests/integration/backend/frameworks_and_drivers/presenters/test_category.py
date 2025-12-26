from typing import Any
from uuid import uuid4

import pytest

from backend.core.application.patterns.use_case_abc import EmptyResponseDTO
from backend.core.application.use_cases.category.dtos import CategoryEntityResponseDTO
from backend.frameworks_and_drivers.di.presenters_container import PresentersContainer
from backend.interface_adapters.patterns.empty_view_model import EmptyViewModel


@pytest.mark.parametrize("dto", [EmptyResponseDTO(), None])
def test_present_empty_view_model(presenters_container: PresentersContainer, dto: Any) -> None:
    # given
    presenter = presenters_container.category_presenter()

    # when
    view_model: EmptyViewModel = presenter.present(dto)

    # then
    assert isinstance(view_model, dict)
    assert not view_model


def test_present_category_response_dto(presenters_container: PresentersContainer) -> None:
    # given
    presenter = presenters_container.category_presenter()
    dto = CategoryEntityResponseDTO(category_uuid=uuid4(), name="test_name", helper_words=frozenset(["a", "b"]))

    # when
    view_model = presenter.present(dto)

    # then
    assert isinstance(view_model, dict)
    assert view_model["category_uuid"] == str(dto.category_uuid)
    assert view_model["name"] == dto.name
    assert view_model["helper_words"] == list(dto.helper_words)
