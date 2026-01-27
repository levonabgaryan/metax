import subprocess
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DJANGO_SERVER_HOST = os.environ.get("DJANGO_SERVER_HOST")
DJANGO_SERVER_PORT = os.environ.get("DJANGO_SERVER_PORT")


def run_server() -> None:
    current_dir = Path(__file__).resolve().parent
    target_dir = current_dir / "frameworks_and_drivers" / "django_framework"

    try:
        if not target_dir.exists():
            print(f"❌ Directory is not found: {target_dir}")
            sys.exit(1)

        os.chdir(target_dir)
        print(f"📂 Switched to: {os.getcwd()}")

        # https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/uvicorn/#running-django-in-uvicorn:~:text=To%20install%20Uvicorn%20and%20Gunicorn%2C%20use%20the%20following%3A
        command = [
            "python",
            "-m",
            "gunicorn",
            "django_framework.asgi:application",
            "-w",
            "2",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "-b",
            f"{DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}",
        ]

        print(f"🚀 Starting Gunicorn on {DJANGO_SERVER_HOST}:{DJANGO_SERVER_PORT}...")
        subprocess.run(command, check=True)

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as ex:
        print(f"💥 Unexpected error: {ex}")
        sys.exit(1)


if __name__ == "__main__":
    run_server()
