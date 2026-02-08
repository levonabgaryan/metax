import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from unittest.mock import Mock
from uuid import uuid4

import pytest
from dependency_injector.wiring import Provide, inject

from discount_service.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from discount_service.core.application.ports.patterns.unit_of_work import AbstractUnitOfWork
from discount_service.core.application.use_cases.discounted_product.dtos import (
    CollectDiscountedProductsFromRetailerRequest,
)

from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct
from discount_service.frameworks_and_drivers.di.bootstrap import ServiceContainer
from django_framework.discount_service.models import RetailerModel, DiscountedProductModel
from tests.integration.conftest import get_current_container
from tests.utils import mock_create_many_discounted_products_from_retailer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@inject
async def test_collect_discounted_products_from_retailer_use_case_saves_products_in_db(
    unit_of_work: AbstractUnitOfWork = Provide[ServiceContainer.patterns_container.container.unit_of_work],
) -> None:
    # given
    retailer_model = await RetailerModel._default_manager.acreate(
        retailer_uuid=uuid4(), name="Test Retailer", url="http://test.com"
    )

    expected_batches = [
        batch
        async for batch in mock_create_many_discounted_products_from_retailer(
            discounted_product_counts=5, retailer_uuid=retailer_model.retailer_uuid
        )
    ]
    expected_products = [p for batch in expected_batches for p in batch]

    async def mock_gen(*args: Any, **kwargs: Any) -> AsyncIterator[list[DiscountedProduct]]:
        for batch in expected_batches:
            yield batch
            await asyncio.sleep(0.0)

    mocked_factory_class = Mock(spec=IDiscountedProductFactory)
    mocked_factory_class.create_many_from_retailer.side_effect = mock_gen

    # when
    started_date = datetime.now(timezone.utc)
    with get_current_container().patterns_container.container.discounted_product_factory.override(
        mocked_factory_class
    ):
        use_case = await get_current_container().use_cases_container.container.discounted_product.container.collect_discounted_products_from_retailer.async_()
        request = CollectDiscountedProductsFromRetailerRequest(
            retailer_url="https://test.com", started_time=started_date
        )
        response = await use_case.execute(request)

    # then
    assert response.added_count == 5

    all_discounted_products = [product async for product in unit_of_work.discounted_product_repo.get_all()]

    discounted_product_models = [
        model async for model in DiscountedProductModel._default_manager.filter(created_at=started_date)
    ]
    for product in discounted_product_models:
        assert product.created_at == started_date

    assert all_discounted_products == expected_products
