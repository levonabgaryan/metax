"""Lightweight checks for Taskiq task metadata (no DB / integration fixtures)."""

from __future__ import annotations

from metax.frameworks_and_drivers.taskiq_framework.tasks import (
    taskiq_collect_discounted_products_for_retailer,
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


def test_collect_for_retailer_task_is_manual_only_with_no_schedule() -> None:
    """The per-retailer task is triggered manually (admin action) — it must carry no cron schedule,
    otherwise it would double-run alongside the nightly all-retailers job."""
    task = taskiq_collect_discounted_products_for_retailer
    assert task.task_name == "CollectDiscountedProductsForRetailer"
    assert "schedule" not in task.labels
