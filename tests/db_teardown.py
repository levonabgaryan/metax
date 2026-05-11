"""Release Django DB pools and connections before pytest-django destroys ``test_*`` databases.

Mitigates ``OperationalError: database ... is being accessed by other users`` when
using PostgreSQL with ``OPTIONS['pool'] = True`` (Django 6 / psycopg_pool).

See Django discussions around lingering connections (e.g. ticket #22420) and
pytest-django teardown ordering.
"""

from __future__ import annotations

import contextlib


def close_django_db_connections_and_pools() -> None:
    """Close psycopg ``ConnectionPool`` (if any) and all Django connection wrappers."""
    from django.db import connections

    for alias in connections:
        wrapper = connections[alias]
        close_pool = getattr(wrapper, "close_pool", None)
        if callable(close_pool):
            with contextlib.suppress(Exception):
                close_pool()
    connections.close_all()
