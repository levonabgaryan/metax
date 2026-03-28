from __future__ import annotations

from metax.frameworks_and_drivers.celery_framework.celery_application import celery_app
from celery.apps.beat import Beat


def run_metax_celery_app() -> None:
    Beat(app=celery_app).run()


if __name__ == "__main__":
    run_metax_celery_app()
