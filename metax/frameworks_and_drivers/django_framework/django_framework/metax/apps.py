from typing import override

from django.apps import AppConfig


class DiscountServiceConfig(AppConfig):
    name = "django_framework.metax"

    @override
    def ready(self) -> None:
        # https://python-dependency-injector.ets-labs.org/examples/django.html#app-config
        from metax.frameworks_and_drivers.di import get_metax_container

        container = get_metax_container()
        container.wire(
            packages=[
                "django_framework.metax.views",
            ]
        )
