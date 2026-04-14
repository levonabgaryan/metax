from typing import cast

from django.apps import apps

from metax_application import MetaxApplication


def get_current_metax_app() -> MetaxApplication:
    django_metax_app = apps.get_app_config("metax")
    metax_app = getattr(django_metax_app, "metax_application", None)
    if metax_app is None:
        msg = "MetaxApplication is not attached to Django app config."
        raise RuntimeError(msg)
    return cast(MetaxApplication, metax_app)
