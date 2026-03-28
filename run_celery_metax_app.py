import asyncio
import sys
from asyncio.subprocess import Process


async def run_celery_worker(concurrency: int = 1) -> Process:
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "metax.frameworks_and_drivers.celery_framework.celery_application",
        "worker",
        "-c",
        str(concurrency),
    ]

    process = await asyncio.create_subprocess_exec(*cmd)
    return process


async def run_celery_beat() -> Process:
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "metax.frameworks_and_drivers.celery_framework.celery_application",
        "beat",
    ]

    process = await asyncio.create_subprocess_exec(*cmd)
    return process


async def run_all_celery() -> None:
    worker = await run_celery_worker(concurrency=2)
    beat = await run_celery_beat()

    await asyncio.gather(worker.wait(), beat.wait())


if __name__ == "__main__":
    asyncio.run(run_all_celery())
