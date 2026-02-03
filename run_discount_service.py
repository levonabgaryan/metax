import os
import subprocess
import sys
from pathlib import Path

from config import discount_service_configs


# -------------------------
# Django
# -------------------------


def run_db_migrations() -> None:
    manage_py = Path(discount_service_configs.django_dir) / "manage.py"

    subprocess.run(
        [sys.executable, str(manage_py), "makemigrations"],
        check=True,
        cwd=discount_service_configs.django_dir,
    )
    subprocess.run(
        [sys.executable, str(manage_py), "migrate"],
        check=True,
        cwd=discount_service_configs.django_dir,
    )


def run_django_uvicorn_server() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(discount_service_configs.project_root_pythonpath)

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
        f"{discount_service_configs.django_host}:{discount_service_configs.django_port}",
    ]

    print(
        f"🚀 Starting Django (Gunicorn + Uvicorn) on {discount_service_configs.django_host}:{discount_service_configs.django_port}"
    )
    print(f"📂 Project root: {discount_service_configs.project_root_pythonpath}")

    subprocess.run(command, check=True, cwd=discount_service_configs.django_dir, env=env)


# -------------------------
# Entry point
# -------------------------


def run_discount_service_app() -> None:
    try:
        run_db_migrations()
        run_django_uvicorn_server()
    except KeyboardInterrupt:
        print("\n🛑 Received KeyboardInterrupt, shutting down gracefully...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Subprocess failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_discount_service_app()
