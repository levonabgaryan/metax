import asyncio
import logging
import sys

logger = logging.getLogger(__name__)


async def run_metax_taskiq_app() -> None:
    taskiq_worker_launch_command = [
        "taskiq",
        "worker",
        "--no-configure-logging",
        "--workers",
        "2",
        "metax.frameworks_and_drivers.taskiq_framework.broker:broker_",
        "metax.frameworks_and_drivers.taskiq_framework.tasks",
    ]

    process = await asyncio.create_subprocess_exec(
        *taskiq_worker_launch_command,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    try:
        await process.wait()
    except asyncio.CancelledError, KeyboardInterrupt:
        if process.returncode is None:
            logger.info("SHUTDOWN | Waiting for Taskiq to stop gracefully...")
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except TimeoutError:
                logger.warning("SHUTDOWN | Taskiq is stuck, force killing...")
                process.kill()
                await process.wait()
    finally:
        logger.info("SHUTDOWN | Metax Taskiq App stopped")


if __name__ == "__main__":
    try:
        asyncio.run(run_metax_taskiq_app())
    except KeyboardInterrupt:
        sys.exit(0)


# to relearn
# Endpoints included, relationship builders
# asyncio, Open-search, subprocess(sync and async), signals

# to implement
# CI/CD UPDATE.
# API tests
