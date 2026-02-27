from django.apps import AppConfig


class DiscountServiceConfig(AppConfig):
    name = "django_framework.discount_service"

    def ready(self) -> None:
        # https://python-dependency-injector.ets-labs.org/examples/django.html#app-config
        from discount_service.frameworks_and_drivers.di.bootstrap import configured_service_container

        container = configured_service_container()
        container.wire(
            packages=[
                "django_framework.discount_service.views",
            ]
        )
