from __future__ import annotations

import os
import sys

from django.apps import AppConfig

from config_ import metax_configs


def create_metax_django_app() -> AppConfig:
    project_root_ = metax_configs.project_root_pythonpath
    django_path_ = metax_configs.django_dir
    sys.path.insert(0, str(project_root_))
    sys.path.insert(0, str(django_path_))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_framework.settings")

    import django
    from django.apps import apps

    django.setup()

    from metax.frameworks_and_drivers.di.metax_container import get_metax_container

    container = get_metax_container()
    metax_app = apps.get_app_config("metax")
    metax_app.container = container  # type: ignore[attr-defined]
    return metax_app
