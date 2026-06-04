"""Single entry point for the full Metax dev stack.

Starts the database containers, waits for them to become healthy, then runs
the HTTP server, taskiq worker, and Telegram bot concurrently in the same
terminal.  Ctrl-C stops everything cleanly.

Usage:
    python run_dev.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent
_COMPOSE_FILE = _ROOT / "docker-compose.dev.yml"
_ENV = {**os.environ, "ENV": "dev"}


def _venv_python() -> str:
    candidates = (
        _ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"),
        _ROOT / ".venv" / "bin" / "python",
        _ROOT / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def _runner_env() -> dict[str, str]:
    env = dict(_ENV)
    venv_bin = _ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    if venv_bin.exists():
        existing_path = env.get("PATH", "")
        env["PATH"] = f"{venv_bin}{os.pathsep}{existing_path}" if existing_path else str(venv_bin)
    return env

_SERVICES = [
    ("HTTP server",     "run_metax_http_server.py"),
    ("Taskiq worker",   "run_metax_taskiq_app.py"),
    ("Telegram bot",    "run_metax_telegram_bot.py"),
]

_HEALTH_POLL_INTERVAL = 2       # seconds between health checks
_HEALTH_TIMEOUT       = 90      # seconds before giving up


# ── docker helpers ────────────────────────────────────────────────────────────

def _docker_up() -> None:
    logger.info("Starting database containers…")
    subprocess.run(
        ["docker", "compose", "-f", str(_COMPOSE_FILE), "up", "-d"],
        check=True,
        env=_ENV,
    )


def _all_healthy() -> bool:
    result = subprocess.run(
        ["docker", "compose", "-f", str(_COMPOSE_FILE), "ps"],
        capture_output=True,
        text=True,
        env=_ENV,
    )
    lines = [l for l in result.stdout.splitlines() if l.strip() and "NAME" not in l]
    return bool(lines) and all("(healthy)" in l for l in lines)


async def _wait_healthy() -> None:
    deadline = asyncio.get_event_loop().time() + _HEALTH_TIMEOUT
    while asyncio.get_event_loop().time() < deadline:
        if _all_healthy():
            logger.info("All containers are healthy.")
            return
        await asyncio.sleep(_HEALTH_POLL_INTERVAL)
    msg = f"Containers did not become healthy within {_HEALTH_TIMEOUT}s."
    raise TimeoutError(msg)


# ── process helpers ───────────────────────────────────────────────────────────

async def _spawn(label: str, script: str) -> asyncio.subprocess.Process:
    proc = await asyncio.create_subprocess_exec(
        _venv_python(),
        str(_ROOT / script),
        cwd=str(_ROOT),
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=_runner_env(),
    )
    logger.info("%-16s started  (pid %d)", label, proc.pid)
    return proc


async def _terminate_all(procs: list[tuple[str, asyncio.subprocess.Process]]) -> None:
    for label, proc in procs:
        if proc.returncode is None:
            proc.terminate()
            logger.info("%-16s → SIGTERM sent", label)
    results = await asyncio.gather(*[p.wait() for _, p in procs], return_exceptions=True)
    for (label, _), rc in zip(procs, results):
        logger.info("%-16s → exited (%s)", label, rc)


# ── main ──────────────────────────────────────────────────────────────────────

async def _run() -> None:
    _docker_up()
    await _wait_healthy()

    procs: list[tuple[str, asyncio.subprocess.Process]] = []
    for label, script in _SERVICES:
        proc = await _spawn(label, script)
        procs.append((label, proc))
        await asyncio.sleep(0.3)   # stagger startup to avoid log noise overlap

    logger.info("Full dev stack running. Press Ctrl-C to stop.")

    wait_tasks = [asyncio.create_task(proc.wait(), name=label) for label, proc in procs]
    try:
        done, _ = await asyncio.wait(wait_tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            rc = task.result()
            if rc not in (0, None, -15):   # -15 = SIGTERM (normal shutdown)
                logger.error("'%s' exited unexpectedly with code %d", task.get_name(), rc)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        for task in wait_tasks:
            task.cancel()
        await _terminate_all(procs)


if __name__ == "__main__":
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(0)
