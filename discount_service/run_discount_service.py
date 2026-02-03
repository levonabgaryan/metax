import subprocess
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# -------------------------
# Paths
# -------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DJANGO_DIR = PROJECT_ROOT / "discount_service" / "frameworks_and_drivers" / "django_framework"
MANAGE_PY = DJANGO_DIR / "manage.py"


# -------------------------
# Environment
# -------------------------


def setup_environment() -> dict[str, str]:
    env_file = PROJECT_ROOT / "discount_service" / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    return env


# -------------------------
# Django
# -------------------------


def run_db_migrations(env_: dict[str, str]) -> None:
    subprocess.run(
        [sys.executable, str(MANAGE_PY), "makemigrations"],
        check=True,
        env=env_,
        cwd=DJANGO_DIR,
    )
    subprocess.run(
        [sys.executable, str(MANAGE_PY), "migrate", "discount_service"],
        check=True,
        env=env_,
        cwd=DJANGO_DIR,
    )


def run_django_uvicorn_server(env_: dict[str, str]) -> None:
    host = env_["DJANGO_SERVER_HOST"]
    port = env_["DJANGO_SERVER_PORT"]

    env_ = env_.copy()
    env_["PYTHONPATH"] = str(DJANGO_DIR)

    command = [
        sys.executable,
        "-m",
        "gunicorn",
        "django_framework.asgi:application",
        "-w",
        "2",
        "-k",
        "uvicorn.workers.UvicornWorker",
        "-b",
        f"{host}:{port}",
    ]

    print(f"🚀 Starting Django (Gunicorn + Uvicorn) on {host}:{port}")
    print(f"📂 Project root: {PROJECT_ROOT}")

    try:
        subprocess.run(
            command,
            check=True,
            env=env_,
            cwd=PROJECT_ROOT,
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as exc:
        print(f"💥 Server crashed: {exc}")
        sys.exit(1)


# -------------------------
# Entry point
# -------------------------


def run_discount_service_app() -> None:
    env = setup_environment()
    run_db_migrations(env)
    run_django_uvicorn_server(env)


if __name__ == "__main__":
    run_discount_service_app()
