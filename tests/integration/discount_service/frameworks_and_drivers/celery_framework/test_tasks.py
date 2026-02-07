# import asyncio
# from typing import AsyncIterator, Any
# from unittest.mock import Mock
#
# import pytest
# from pytest_celery.api.worker import CeleryTestWorker
#
# from discount_service.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
# from discount_service.core.application.ports.repositories.entites_repositories.retailer import RetailerRepository
# from discount_service.core.domain.entities.discounted_product_entity.discounted_product import DiscountedProduct
# from tests.integration.conftest import get_current_container
# from tests.utils import mock_create_many_discounted_products_from_retailer, make_retailer_entity
#
#
# async def test_collect_discounted_products_from_retailer_success(celery_worker: CeleryTestWorker) -> None:
#     # given
#     mocked_retailer_repo = Mock(spec=RetailerRepository)
#     mocked_retailer_repo.get_all_retailers_urls.return_value = ["test_url"]
#
#     retailer = make_retailer_entity()
#     batches = [
#         batch
#         async for batch in mock_create_many_discounted_products_from_retailer(
#             discounted_product_counts=5, retailer_uuid=retailer.get_uuid()
#         )
#     ]
#
#     async def mock_gen(*args: Any, **kwargs: Any) -> AsyncIterator[list[DiscountedProduct]]:
#         for batch in batches:
#             yield batch
#             await asyncio.sleep(0.0)
#
#     mocked_factory_class = Mock(spec=IDiscountedProductFactory)
#     mocked_factory_class.create_many_from_retailer.side_effect = mock_gen
#
#     with (
#         get_current_container().patterns_container.container.discounted_product_factory.override(
#             mocked_factory_class
#     ),
#         get_current_container()
#     ):
#         pass
#
#
