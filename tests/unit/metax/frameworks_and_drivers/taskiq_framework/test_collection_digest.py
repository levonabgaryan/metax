import datetime as dt
from decimal import Decimal

from metax.frameworks_and_drivers.taskiq_framework.collection_digest import (
    ProductSample,
    RetailerCrawlOutcome,
    format_crawl_digest,
)

_RUN_DATE = dt.datetime(2026, 7, 8, tzinfo=dt.UTC)


def _digest(*outcomes: RetailerCrawlOutcome) -> str:
    return format_crawl_digest(list(outcomes), run_date=_RUN_DATE)


def test_header_shows_run_date() -> None:
    assert "2026-07-08" in _digest(RetailerCrawlOutcome(name="sas-am", previous=100, extracted=100))


def test_small_change_is_healthy() -> None:
    # +5% is within normal night-to-night drift.
    line = _digest(RetailerCrawlOutcome(name="sas-am", previous=800, extracted=840))
    assert "✅" in line
    assert "⚠️" not in line
    assert "+5%" in line


def test_big_drop_is_flagged() -> None:
    line = _digest(RetailerCrawlOutcome(name="sas-am", previous=800, extracted=400))
    assert "⚠️" in line
    assert "-50%" in line


def test_big_jump_is_flagged() -> None:
    assert "⚠️" in _digest(RetailerCrawlOutcome(name="sas-am", previous=100, extracted=200))


def test_zero_collected_with_history_is_a_break() -> None:
    line = _digest(RetailerCrawlOutcome(name="tntesakan-am", previous=214, extracted=0))
    assert "⚠️" in line
    assert "BROKE" in line
    assert "prev 214" in line


def test_collector_error_is_distinct_from_zero() -> None:
    line = _digest(RetailerCrawlOutcome(name="rouge-am", previous=383, extracted=None))
    assert "❌" in line
    assert "collector failed" in line
    assert "prev 383" in line


def test_first_run_has_no_baseline_to_compare() -> None:
    line = _digest(RetailerCrawlOutcome(name="newshop-am", previous=0, extracted=40))
    assert "🆕" in line
    assert "new" in line


def test_sample_product_is_rendered_with_link_prices_and_image() -> None:
    digest = _digest(
        RetailerCrawlOutcome(
            name="sas-am",
            previous=806,
            extracted=812,
            sample=ProductSample(
                name="Coca-Cola 1L",
                real_price=Decimal("450"),
                discounted_price=Decimal("390"),
                url="https://www.sas.am/p/1",
                image_url="https://img/1.png",
            ),
        )
    )
    assert '<a href="https://www.sas.am/p/1">Coca-Cola 1L</a>' in digest
    assert "450→390" in digest
    assert "🖼" in digest


def test_sample_without_image_is_flagged() -> None:
    digest = _digest(
        RetailerCrawlOutcome(
            name="sas-am",
            previous=806,
            extracted=812,
            sample=ProductSample(
                name="No Photo Item",
                real_price=Decimal("1000"),
                discounted_price=Decimal("800"),
                url="https://www.sas.am/p/2",
                image_url=None,
            ),
        )
    )
    assert "no image" in digest


def test_one_line_per_retailer() -> None:
    digest = _digest(
        RetailerCrawlOutcome(name="sas-am", previous=800, extracted=810),
        RetailerCrawlOutcome(name="rouge-am", previous=383, extracted=385),
    )
    for name in ("sas-am", "rouge-am"):
        assert digest.count(name) == 1
