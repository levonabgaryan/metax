import re
import subprocess  # noqa: S404
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from typer import Exit, Option, Typer, echo

from metax_bootstrap import METAX_CONFIGS

migrations = Typer(name="migrations")

_NOT_IDENTIFIER_CHAR = re.compile(r"[^a-zA-Z0-9_]+")


def _django_migration_name_slug(user_part: str, timestamp: str) -> str:
    """Build a ``makemigrations --name`` value (must be a valid Python identifier).

    Returns:
        Identifier-safe string ``{slug}_{timestamp}`` starting with a letter or underscore
        (timestamp like ``2026_05_02_14_30``).
    """
    slug = user_part.strip().replace(" ", "_")
    slug = _NOT_IDENTIFIER_CHAR.sub("_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_").lower()
    if not slug:
        slug = "migration"
    # Identifiers cannot start with a digit — prefix so ``2026…`` timestamps never lead.
    if slug[0].isdigit():
        slug = f"m_{slug}"
    return f"{slug}_{timestamp}"


@migrations.command()
def migrate_postgres(
    migration_name: Annotated[str, Option(prompt=True)],
) -> None:

    timestamp = datetime.now(tz=UTC).strftime("%Y_%m_%d_%H_%M")
    full_migration_name = _django_migration_name_slug(migration_name, timestamp)
    manage_py = Path(METAX_CONFIGS.django_dir) / "manage.py"
    echo("STARTUP | Task: Postgres Migrations | Status: Started")
    make = subprocess.run(  # noqa: S603
        [sys.executable, str(manage_py), "makemigrations", "metax", "--name", full_migration_name],
        cwd=METAX_CONFIGS.django_dir,
        check=False,
    )
    if make.returncode != 0:
        echo(f"STARTUP | Task: Postgres Migrations | Status: FAILED at makemigrations | Code: {make.returncode}")
        raise Exit(code=make.returncode)

    apply = subprocess.run(  # noqa: S603
        [sys.executable, str(manage_py), "migrate", "metax"],
        cwd=METAX_CONFIGS.django_dir,
        check=False,
    )
    if apply.returncode != 0:
        echo(f"STARTUP | Task: Postgres Migrations | Status: FAILED at migrate | Code: {apply.returncode}")
        raise Exit(code=apply.returncode)

    echo("STARTUP | Task: Postgres Migrations | Status: SUCCESS")
