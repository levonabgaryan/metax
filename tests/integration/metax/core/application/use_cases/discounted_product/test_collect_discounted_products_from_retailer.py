# from datetime import datetime, timezone
# from unittest.mock import MagicMock
#
# import pytest
#
# from metax.core.application.use_cases.discounted_product.dtos import (
#     CollectDiscountedProductsFromRetailerRequest,
# )
# from metax.frameworks_and_drivers.di.bootstrap import MetaxContainer
# from tests.utils import make_retailer_entity, __aiter_wrapper
#
#
# @pytest.mark.django_db(transaction=True)
# @pytest.mark.asyncio
# async def test_collect_discounted_products_from_retailer_use_case_saves_products_in_db(
#     service_container_for_tests: ServiceContainer,
# ) -> None:
#     # given
#     unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
#     retailer = make_retailer_entity()
#
#     await unit_of_work.retailer_repo.add(retailer)
#     scrapper_mock = MagicMock()
#     mock_data = [
#         {"name": "lays", "real_price": "850", "discounted_price": "650.0", "url": "http://test.com/1"},
#         {"name": "cola", "real_price": "450.0", "discounted_price": 350, "url": "http://test.com/2"},
#     ]
#     scrapper_mock.fetch.side_effect = lambda: __aiter_wrapper(mock_data)
#
#     # when
#     started_date = datetime.now(tz=timezone.utc)
#     request = CollectDiscountedProductsFromRetailerRequest(started_time=started_date)
#
#     with metax_container_for_integration_tests.patterns_container.container.discounted_product_factory.override(
#         mocked_factory_class
#     ):
#         use_case = await metax_container_for_integration_tests.use_cases_container.container.discounted_product.container.collect_discounted_products_from_retailer.async_()
#         request = CollectDiscountedProductsFromRetailerRequest(started_time=started_date)
#         response = await use_case.execute(request)
#
#     # then
#     assert response.added_count == 5
#
#     all_discounted_products = [product async for product in unit_of_work.discounted_product_repo.get_all()]
#
#     discounted_product_models = [
#         model async for model in DiscountedProductModel._default_manager.filter(created_at=started_date)
#     ]
#     for product in discounted_product_models:
#         assert product.created_at == started_date
#
#     assert all_discounted_products == expected_products
