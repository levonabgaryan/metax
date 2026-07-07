"""A single global Redis lock serializing the crawl collect → embed → publish lifecycle.

Why global (not per-retailer): the nightly all-retailers run's publish swap deletes rows across
*every* retailer at once, so any manual single-retailer run overlapping it could have its freshly
collected rows wiped — or wipe the nightly run's. A per-retailer lock cannot protect a cross-retailer
delete, so every crawl job (nightly or manual) contends for the same lock. Serializing crawls is
acceptable: they are infrequent and a queued run simply starts once the running one releases.

Why it spans two jobs: the destructive step (publish) happens in the *embed* job, which is a separate
TaskIQ job from collection. The collection job acquires the lock and hands its release token to the
embed job, which releases it after publishing. A TTL guarantees the lock is freed even if the embed
job never runs (e.g. it was never enqueued because the collection job crashed).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from redis.asyncio import Redis

from metax_bootstrap import METAX_CONFIGS

if TYPE_CHECKING:
    from redis.commands.core import AsyncScript

_LOCK_KEY = "metax:collection:lock"

# Release only if we still own the lock: delete the key solely when its value matches our token. This
# prevents a job whose lock already expired (TTL elapsed mid-run) from deleting the lock that a
# *different* run has since acquired. Kept atomic via a server-side Lua script.
_RELEASE_IF_OWNER_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""


class CollectionLock:
    """Non-blocking global lock for the crawl lifecycle. One instance per process is enough."""

    def __init__(self, redis_url: str, ttl_seconds: int, client: Redis | None = None) -> None:
        self.__redis_url = redis_url
        self.__ttl_seconds = ttl_seconds
        self.__client = client

    def __get_client(self) -> Redis:
        if self.__client is None:
            self.__client = Redis.from_url(self.__redis_url)
        return self.__client

    async def acquire(self) -> str | None:
        """Try to take the lock without blocking.

        Returns:
            An opaque release token if the lock was taken, or ``None`` if another run already holds
            it (the caller should skip). The token must be passed to :meth:`release`.
        """
        token = uuid.uuid4().hex
        acquired = await self.__get_client().set(_LOCK_KEY, token, nx=True, ex=self.__ttl_seconds)
        return token if acquired else None

    async def release(self, token: str) -> None:
        """Release the lock, but only if ``token`` still owns it (see ``_RELEASE_IF_OWNER_LUA``)."""
        release_script: AsyncScript = self.__get_client().register_script(_RELEASE_IF_OWNER_LUA)
        await release_script(keys=[_LOCK_KEY], args=[token])


_collection_lock: CollectionLock | None = None


def get_collection_lock() -> CollectionLock:
    """Return the process-wide :class:`CollectionLock`, building it lazily on first use."""
    global _collection_lock
    if _collection_lock is None:
        _collection_lock = CollectionLock(
            redis_url=METAX_CONFIGS.redis_url,
            ttl_seconds=METAX_CONFIGS.collection_lock_ttl_seconds,
        )
    return _collection_lock
