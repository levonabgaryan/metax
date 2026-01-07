import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator
from unittest.mock import Mock
from uuid import uuid4

import pytest

from backend.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
from backend.core.application.ports.patterns.unit_of_work import UnitOfWork
from backend.core.application.use_cases.discounted_product.dtos import CollectDiscountedProductsFromRetailerRequest
from backend.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct
from backend.frameworks_and_drivers.di.use_cases_container import DiscountedProductUseCasesContainer
from django_framework.discount_service.models import RetailerModel, DiscountedProductModel
from tests.integration.conftest import mock_create_many_discounted_products_from_retailer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_collect_discounted_products_from_retailer_use_case_saves_products_in_db(
    discounted_product_use_cases: DiscountedProductUseCasesContainer,
    unit_of_work: UnitOfWork,
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
    with discounted_product_use_cases.patterns().discounted_product_factory.override(mocked_factory_class):
        use_case = discounted_product_use_cases.collect_discounted_products_from_retailer()
        request = CollectDiscountedProductsFromRetailerRequest(
            retailer_url="http://test.com", started_time=started_date
        )
        response = await use_case.execute(request)

    # then
    assert response.added_count == 5

    async with unit_of_work as uow:
        all_discounted_products = [product async for product in uow.repositories.discounted_product.get_all()]
        await uow.commit()

    discounted_product_models = [
        model async for model in DiscountedProductModel._default_manager.filter(created_at=started_date)
    ]
    for product in discounted_product_models:
        assert product.created_at == started_date

    assert all_discounted_products == expected_products
