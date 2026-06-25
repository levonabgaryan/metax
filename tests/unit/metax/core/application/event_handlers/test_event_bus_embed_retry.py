"""Unit tests for the embed-handler retry logic in ``EventBus`` (no DB / embeddings service).

``OldDiscountedProductsDeleted`` triggers embedding, which calls the embeddings service and can
transiently fail (e.g. a ReadTimeout while the model loads on a cold start). The handler retries
because ``embed_pending`` is idempotent — a retry only re-fetches still-unembedded rows.
"""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock

import pytest

import metax.core.application.event_handlers.event_bus as event_bus_module
from metax.core.application.event_handlers.discounted_product.events import OldDiscountedProductsDeleted
from metax.core.application.event_handlers.event_bus import EventBus


@pytest.fixture(autouse=True)
def _no_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep retries instant so the tests don't actually sleep."""
    monkeypatch.setattr(event_bus_module, "_EMBED_RETRY_BACKOFF_SECONDS", 0.0)


def _make_bus(repo: AsyncMock) -> EventBus:
    return EventBus(unit_of_work_provider=AsyncMock(), discounted_product_read_model_repo=repo)


def _event() -> OldDiscountedProductsDeleted:
    return OldDiscountedProductsDeleted(new_discounted_products_creation_date=dt.datetime.now(dt.UTC))


async def test_embed_handler_retries_until_success() -> None:
    # given: two transient failures, then a successful embed of 42 rows
    repo = AsyncMock()
    repo.embed_pending.side_effect = [TimeoutError("cold start"), TimeoutError("cold start"), 42]
    bus = _make_bus(repo)

    # when
    await bus._EventBus__embed_new_discounted_products(_event())  # type: ignore[attr-defined]  # noqa: SLF001

    # then: it kept retrying and eventually succeeded
    assert repo.embed_pending.await_count == 3


async def test_embed_handler_raises_after_exhausting_retries() -> None:
    # given: embedding fails on every attempt
    repo = AsyncMock()
    repo.embed_pending.side_effect = TimeoutError("embeddings service down")
    bus = _make_bus(repo)

    # when / then: the failure is surfaced after the attempt budget is spent
    with pytest.raises(RuntimeError, match="failed after 3 attempts"):
        await bus._EventBus__embed_new_discounted_products(_event())  # type: ignore[attr-defined]  # noqa: SLF001
    assert repo.embed_pending.await_count == event_bus_module._EMBED_MAX_ATTEMPTS  # noqa: SLF001


async def test_embed_handler_succeeds_first_try_without_retry() -> None:
    # given: embedding succeeds immediately
    repo = AsyncMock()
    repo.embed_pending.return_value = 7
    bus = _make_bus(repo)

    # when
    await bus._EventBus__embed_new_discounted_products(_event())  # type: ignore[attr-defined]  # noqa: SLF001

    # then: no retry happened
    assert repo.embed_pending.await_count == 1
