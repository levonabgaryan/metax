# from datetime import datetime, timezone
# from decimal import Decimal
# from unittest.mock import MagicMock
#
# import pytest
#
# from metax.frameworks_and_drivers.di import ServiceContainer
#
# from tests.utils import __aiter_wrapper, make_retailer_entity
# from constants import RetailersNames
#
#
# @pytest.mark.django_db(transaction=True)
# @pytest.mark.asyncio
# async def test_yerevan_city_collector_service(service_container_for_tests: ServiceContainer) -> None:
#     # given
#     unit_of_work = await service_container_for_tests.patterns_container.container.unit_of_work.async_()
#     retailer = make_retailer_entity(name=RetailersNames.YEREVAN_CITY)
#     await unit_of_work.retailer_repo.add(retailer)
#
#     started_time = datetime.now(tz=timezone.utc)
#     yerevan_city_scrapper_mock = MagicMock()
#     mock_data = [
#         {"name": "lays", "real_price": "850", "discounted_price": "650.0", "url": "http://test.com/1"},
#         {"name": "cola", "real_price": "450.0", "discounted_price": 350, "url": "http://test.com/2"},
#     ]
#     yerevan_city_scrapper_mock.fetch.side_effect = lambda: __aiter_wrapper(mock_data)
#
#     # when
#     with (
#         service_container_for_tests.scrappers_adapters_container.container.yerevan_city_scrapper_adapter.override(
#             yerevan_city_scrapper_mock
#         ),
#     ):
#         yerevan_city_discounted_products_collector_service = await service_container_for_tests.discounted_products_collector_services_container.
#         await yerevan_city_discounted_products_collector_service.collect_from_retailer_and_return_collected_count(
#             started_time_of_collected=started_time
#         )
#
#     # then
#     discounted_products = unit_of_work.discounted_product_repo.get_all()
#
#     count = 0
#     async for discounted_product in discounted_products:
#         assert discounted_product.get_retailer_uuid() == retailer.get_uuid()
#         assert discounted_product.get_name() in {"lays", "cola"}
#         if discounted_product.get_name() == "lays":
#             assert discounted_product.get_discounted_price() == Decimal("650.00")
#         if discounted_product.get_name() == "cola":
#             assert discounted_product.get_discounted_price() == Decimal("350.00")
#         count += 1
#
#     assert count == 2
