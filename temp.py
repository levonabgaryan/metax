# from datetime import datetime
# from pprint import pprint
# from discount_service.core.application.ports.patterns.discounted_product_factory import IDiscountedProductFactory
# import asyncio
#
# from discount_service.frameworks_and_drivers.di import get_service_container
#
#
# async def main() -> None:
#     import os
#
#     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "discount_service.frameworks_and_drivers.django_framework.django_framework.settings")
#
#     import django
#
#     django.setup()
#     container = get_service_container()
#
#     # Resource создаётся через async context manager
#     async with container.discounted_product_factories_container.container.yerevan_city_discounted_product_factory.async_() as factory:
#         async for products in factory.create_many_from_retailer(started_time=datetime.now()):
#             pprint(products)
#
# if __name__ == '__main__':
#     asyncio.run(main())
