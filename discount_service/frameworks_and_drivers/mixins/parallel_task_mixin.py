import asyncio
from typing import Awaitable, AsyncIterator


class ParallelTasksMixin[T]:
    def __init__(self, max_concurrency: int = 50):
        self._max_concurrency = max_concurrency
        self._semaphore: asyncio.Semaphore | None = None

    @property
    def semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrency)
        return self._semaphore

    async def run_parallel_coroutines(
        self, coroutines: list[Awaitable[T]], batch_size: int = 500
    ) -> AsyncIterator[list[T]]:
        if not coroutines:
            return

        pending_tasks: set[asyncio.Task[T]] = {
            asyncio.create_task(self._run_with_semaphore(c)) for c in coroutines
        }
        batch: list[T] = []

        while pending_tasks:
            done, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                try:
                    result = task.result()
                    batch.append(result)
                except Exception as e:
                    print(f"Task error: {e}")

                if len(batch) >= batch_size:
                    yield batch
                    batch = []

        if batch:
            yield batch

    async def _run_with_semaphore(self, coro: Awaitable[T]) -> T:
        async with self.semaphore:
            return await coro
