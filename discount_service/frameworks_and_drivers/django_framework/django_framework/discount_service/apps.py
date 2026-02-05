from django.apps import AppConfig
from discount_service.frameworks_and_drivers.di import get_service_container


class DiscountServiceConfig(AppConfig):
    name = "django_framework.discount_service"

    def ready(self) -> None:
        # https://python-dependency-injector.ets-labs.org/examples/django.html#app-config
        container = get_service_container()
        container.wire(
            packages=[
                "django_framework.discount_service.views",
            ]
        )
