"""Lightweight checks for Taskiq task metadata (no DB / integration fixtures)."""

from __future__ import annotations

from metax.frameworks_and_drivers.taskiq_framework.tasks import (
    taskiq_collect_discounted_products_from_all_retailers,
)


def test_collect_discounted_products_scheduled_21_00_utc() -> None:
    """Regression: cron in code; TaskiqScheduler treats unspecified tz as UTC (see broker module)."""
    task = taskiq_collect_discounted_products_from_all_retailers
    assert task.task_name == "CollectDiscountedProducts"
    assert task.labels["schedule"] == [
        {
            "cron": "0 21 * * *",
            "args": [None],
        }
    ]
