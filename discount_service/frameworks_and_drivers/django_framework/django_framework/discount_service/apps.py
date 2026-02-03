from django.apps import AppConfig
from django.conf import settings
from django_framework.di import init_container


class DiscountServiceConfig(AppConfig):
    name = "django_framework.discount_service"

    def ready(self) -> None:
        # https://python-dependency-injector.ets-labs.org/examples/django.html#app-config
        container = init_container()
        container.config.from_dict(settings.__dict__)
        container.wire(
            packages=[
                "django_framework.discount_service.views",
            ]
        )
