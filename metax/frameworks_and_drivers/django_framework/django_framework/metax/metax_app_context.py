from typing import cast

from django.apps import apps

from metax_application_manager import MetaxApplicationManager


def get_current_metax_app() -> MetaxApplicationManager:
    django_metax_app = apps.get_app_config("metax")
    metax_app = getattr(django_metax_app, "metax_application", None)
    if metax_app is None:
        msg = "MetaxApplicationManager is not attached to Django app config."
        raise RuntimeError(msg)
    return cast(MetaxApplicationManager, metax_app)
