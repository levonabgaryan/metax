"""Unit tests for the step 2 (embedding) multi-pass logic (no DB / embeddings service).

Embedding calls the embeddings service, which can transiently fail (e.g. a ReadTimeout while the
model loads on a cold start). ``embed_all_pending`` re-scans for still-unembedded rows because
``embed_pending`` is idempotent — a pass only re-fetches rows whose embedding is still NULL — and
surfaces the failure once the pass budget is spent so TaskIQ marks the embedding job failed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import metax.frameworks_and_drivers.taskiq_framework.tasks as tasks_module
from metax.frameworks_and_drivers.taskiq_framework.tasks import embed_all_pending


@pytest.fixture(autouse=True)
def _no_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep retries instant so the tests don't actually sleep."""
    monkeypatch.setattr(tasks_module, "_EMBED_RETRY_BACKOFF_SECONDS", 0.0)


async def test_embed_succeeds_first_pass_without_rescan() -> None:
    # given: a single pass embeds everything, nothing left pending
    repo = AsyncMock()
    repo.embed_pending.return_value = 7
    repo.count_pending.return_value = 0

    # when
    embedded = await embed_all_pending(repo)

    # then: no extra pass happened
    assert embedded == 7
    assert repo.embed_pending.await_count == 1


async def test_embed_rescans_until_no_rows_pending() -> None:
    # given: two passes each fail partway (rows still pending), the third clears the backlog
    repo = AsyncMock()
    repo.embed_pending.side_effect = [TimeoutError("cold start"), TimeoutError("cold start"), 42]
    repo.count_pending.side_effect = [10, 5, 0]

    # when
    embedded = await embed_all_pending(repo)

    # then: it kept re-scanning and eventually drained the backlog
    assert embedded == 42
    assert repo.embed_pending.await_count == 3


async def test_embed_raises_when_rows_remain_after_pass_budget() -> None:
    # given: embedding never manages to clear the backlog
    repo = AsyncMock()
    repo.embed_pending.side_effect = TimeoutError("embeddings service down")
    repo.count_pending.return_value = 3

    # when / then: the failure is surfaced once the pass budget is spent
    with pytest.raises(RuntimeError, match="3 row\\(s\\) still unembedded after 3 passes"):
        await embed_all_pending(repo)
    assert repo.embed_pending.await_count == tasks_module._EMBED_MAX_PASSES  # noqa: SLF001
