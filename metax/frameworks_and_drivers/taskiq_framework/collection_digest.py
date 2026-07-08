"""Formatting for the nightly crawl health digest.

Pure, side-effect-free helpers so the "big change" logic is unit-testable in isolation from the crawl
job and Telegram. The digest is a quick daily glance: one row per retailer comparing what the run just
collected (``extracted``) against the previous run's set it replaces (``previous``), with a glyph that
makes a break or a big swing jump out.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from html import escape

# A retailer whose count moved by at least this fraction vs. the previous run is flagged for a look.
# Scrapers usually drift a few percent night to night; a 40%+ jump means something changed.
BIG_CHANGE_RATIO = 0.4


@dataclass(frozen=True)
class ProductSample:
    """A single collected product, shown under its retailer so extracted data can be eyeballed.

    Lets an obviously broken field surface at a glance — a phone number where the name should be,
    swapped or zero prices, a missing image — without having to open the site.
    """

    name: str
    real_price: Decimal
    discounted_price: Decimal
    url: str
    image_url: str | None


@dataclass(frozen=True)
class RetailerCrawlOutcome:
    """One retailer's result from a crawl run.

    ``extracted`` is ``None`` when the collector raised (the crawl failed for that retailer), which is
    reported distinctly from a collector that ran fine but returned zero products. ``sample`` is one
    arbitrary product from this run (``None`` when nothing was collected).
    """

    name: str
    previous: int
    extracted: int | None
    sample: ProductSample | None = None


def _classify(extracted: int | None, previous: int) -> tuple[str, str]:
    """Return the ``(glyph, note)`` for a row based on how far ``extracted`` moved from ``previous``."""
    if extracted == 0 and previous > 0:
        return "⚠️", "BROKE — 0 collected"
    if previous == 0:
        # First run for this retailer (or a recovery from an empty state) — nothing to compare against.
        return "🆕", "new"
    change = (extracted - previous) / previous  # type: ignore[operator]  # extracted is not None here
    glyph = "⚠️" if abs(change) >= BIG_CHANGE_RATIO else "✅"
    return glyph, f"{change:+.0%}"


def format_crawl_digest(
    outcomes: list[RetailerCrawlOutcome],
    run_date: dt.datetime,
    *,
    title: str = "🌙 <b>Nightly crawl</b>",
) -> str:
    """Build the HTML message body for a crawl digest — one line per retailer.

    ``title`` heads the message so a manual single-retailer run reads distinctly from the nightly one.

    Returns:
        A Telegram-HTML string; rows with a break or a big swing lead with a warning glyph.
    """
    lines = [f"{title} — {run_date:%Y-%m-%d}", ""]
    for outcome in outcomes:
        name = escape(outcome.name)
        if outcome.extracted is None:
            # Collector raised — reported distinctly from a clean run that returned zero.
            lines.append(f"❌ <b>{name}</b> — collector failed (prev {outcome.previous:,})")
            continue
        glyph, note = _classify(outcome.extracted, outcome.previous)
        lines.append(
            f"{glyph} <b>{name}</b> — {outcome.extracted:,} (prev {outcome.previous:,}, {note})"
        )
        if outcome.sample is not None:
            lines.append(_format_sample(outcome.sample))
    return "\n".join(lines)


def _format_sample(sample: ProductSample) -> str:
    """Render the indented sample-product line: a linked name, its prices, and an image indicator.

    Returns:
        A Telegram-HTML line linking the product name to its page, with ``real→discounted`` prices.
    """
    image_marker = "🖼" if sample.image_url else "🚫 no image"
    real = f"{int(sample.real_price):,}"
    discounted = f"{int(sample.discounted_price):,}"
    return (
        f'    ↳ <a href="{escape(sample.url)}">{escape(sample.name)}</a> — '
        f"{real}→{discounted} ֏ · {image_marker}"
    )
