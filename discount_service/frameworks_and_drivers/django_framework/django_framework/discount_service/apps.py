from django.apps import AppConfig
from django_framework.di import init_container


class DiscountServiceConfig(AppConfig):
    name = "django_framework.discount_service"

    def ready(self) -> None:
        # https://python-dependency-injector.ets-labs.org/examples/django.html#app-config
        container = init_container()
        container.wire(
            packages=[
                "django_framework.discount_service.views",
            ]
        )
