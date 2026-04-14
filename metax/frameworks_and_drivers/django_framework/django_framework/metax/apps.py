from typing import override

from django.apps import AppConfig
from django_asgi_lifespan.register import register_lifespan_manager
from django_framework.metax.lifespan import app_lifespan_manager


class DiscountServiceConfig(AppConfig):
    name = "django_framework.metax"

    @override
    def ready(self) -> None:
        register_lifespan_manager(context_manager=app_lifespan_manager)
