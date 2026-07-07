"""Unit tests for the global collection lock and the crawl-job guard that uses it (no Redis / DB).

The lock serializes the whole collect → embed → publish lifecycle across every crawl job, so a manual
single-retailer run can never overlap the nightly all-retailers run (whose publish swap deletes rows
across all retailers). See ``taskiq_framework/locks.py``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import metax.frameworks_and_drivers.taskiq_framework.tasks as tasks_module
from metax.frameworks_and_drivers.taskiq_framework.locks import CollectionLock


def _make_lock(client: MagicMock) -> CollectionLock:
    return CollectionLock(redis_url="redis://unused", ttl_seconds=3600, client=client)


async def test_acquire_returns_token_using_set_nx_ex() -> None:
    # given: SET NX succeeds (no one holds the lock)
    client = MagicMock()
    client.set = AsyncMock(return_value=True)

    # when
    token = await _make_lock(client).acquire()

    # then: a token is returned and the lock was set atomically with NX + a TTL
    assert token is not None
    _, kwargs = client.set.call_args
    assert kwargs["nx"] is True
    assert kwargs["ex"] == 3600


async def test_acquire_returns_none_when_lock_already_held() -> None:
    # given: SET NX fails (someone else holds the lock)
    client = MagicMock()
    client.set = AsyncMock(return_value=None)

    # when / then
    assert await _make_lock(client).acquire() is None


async def test_release_runs_owner_checked_script_with_token() -> None:
    # given
    client = MagicMock()
    release_script = AsyncMock()
    client.register_script = MagicMock(return_value=release_script)

    # when
    await _make_lock(client).release("my-token")

    # then: the release is delegated to the owner-checking Lua script, keyed by our token
    _, kwargs = release_script.call_args
    assert kwargs["args"] == ["my-token"]


class _FakeLock:
    """Stand-in for :class:`CollectionLock` recording acquire/release calls."""

    def __init__(self, acquire_result: str | None) -> None:
        self.__acquire_result = acquire_result
        self.released_tokens: list[str] = []

    async def acquire(self) -> str | None:
        return self.__acquire_result

    async def release(self, token: str) -> None:
        self.released_tokens.append(token)


@pytest.fixture
def _mock_container(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch the lifespan manager to hand out a mock DI container for the collection closures.

    Returns:
        The mock container the patched lifespan manager will return.
    """
    container = MagicMock()
    container.get_event_bus = AsyncMock()
    monkeypatch.setattr(
        tasks_module.METAX_LIFESPAN_MANAGER, "get_metax_container", lambda: container
    )
    return container


async def test_collection_run_skipped_when_lock_already_held(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # given: the lock is already held (acquire returns None)
    fake_lock = _FakeLock(None)
    monkeypatch.setattr(tasks_module, "get_collection_lock", lambda: fake_lock)
    collect = AsyncMock()
    monkeypatch.setattr(tasks_module, "collect_discounted_products_from_all_retailers", collect)

    # when
    await tasks_module._taskiq_collect_discounted_products_from_all_retailers(request_id="rid")  # noqa: SLF001

    # then: no collection happened and there was no lock we owned to release
    collect.assert_not_awaited()
    assert fake_lock.released_tokens == []


async def test_collection_hands_lock_to_embed_job_without_releasing_it(
    monkeypatch: pytest.MonkeyPatch,
    _mock_container: MagicMock,
) -> None:
    # given: the lock is acquired and embedding runs after collection
    held = "tok-123"
    fake_lock = _FakeLock(held)
    monkeypatch.setattr(tasks_module, "get_collection_lock", lambda: fake_lock)
    monkeypatch.setattr(tasks_module.METAX_CONFIGS, "embed_after_collect", True)
    monkeypatch.setattr(
        tasks_module, "collect_discounted_products_from_all_retailers", AsyncMock()
    )
    embed_task = MagicMock()
    embed_task.kiq = AsyncMock()
    monkeypatch.setattr(tasks_module, "taskiq_embed_discounted_products", embed_task)

    # when
    await tasks_module._taskiq_collect_discounted_products_from_all_retailers(request_id="rid")  # noqa: SLF001

    # then: the token is handed to step 2 and NOT released here (step 2 owns it now)
    _, kwargs = embed_task.kiq.call_args
    assert kwargs["lock_token"] == held
    assert fake_lock.released_tokens == []


async def test_collection_releases_lock_when_embedding_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    _mock_container: MagicMock,
) -> None:
    # given: the lock is acquired but there is no step-2 handoff (EMBED_AFTER_COLLECT off)
    held = "tok-xyz"
    fake_lock = _FakeLock(held)
    monkeypatch.setattr(tasks_module, "get_collection_lock", lambda: fake_lock)
    monkeypatch.setattr(tasks_module.METAX_CONFIGS, "embed_after_collect", False)
    monkeypatch.setattr(
        tasks_module, "collect_discounted_products_from_all_retailers", AsyncMock()
    )

    # when
    await tasks_module._taskiq_collect_discounted_products_from_all_retailers(request_id="rid")  # noqa: SLF001

    # then: with nobody to hand the lock to, this job releases it itself
    assert fake_lock.released_tokens == [held]
