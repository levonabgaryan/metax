from typing import cast

from django.apps import apps

from metax_lifespan import MetaxAppLifespanManager


def get_current_metax_app() -> MetaxAppLifespanManager:
    django_metax_app = apps.get_app_config("metax")
    metax_app = getattr(django_metax_app, "metax_application", None)
    if metax_app is None:
        msg = "AppLifespanManager is not attached to Django app config."
        raise RuntimeError(msg)
    return cast(MetaxAppLifespanManager, metax_app)
