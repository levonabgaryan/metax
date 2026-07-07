"""Application configuration.

Three environments are supported, selected via the ``ENV`` environment variable:

* ``dev``  - run the metax application on the host (outside Docker). Database
             containers are spun up via ``docker-compose.dev.yml``. ``DevConfigs``
             does NOT read any ``.env`` file: class-level defaults below are the
             single source of truth and they must stay in sync with
             ``docker-compose.dev.yml``.
* ``test`` - CI / integration tests. The whole stack runs in Docker via
             ``docker-compose.test.yml``; every required env var is hardcoded in
             that file's ``x-metax-env`` block and pushed into the container.
             ``TestConfigs`` keeps class-level defaults as a safety net for unit
             tests that import the config directly (no compose involved); the
             defaults must mirror ``docker-compose.test.yml``.
* ``prod`` - production. The whole stack runs in Docker via
             ``docker-compose.prod.yml``; every required env var is interpolated
             from the host ``.env`` into the container via the ``environment:``
             block. ``ProdConfigs`` has NO defaults for app-level values: any
             missing variable triggers a Pydantic ValidationError at startup —
             this is intentional ("fail loudly").
"""

import multiprocessing
import os
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfigs(BaseSettings):
    debug: bool

    postgres_user: Annotated[str, Field(alias="POSTGRES_USER")]
    postgres_password: Annotated[str, Field(alias="POSTGRES_PASSWORD")]
    postgres_db: Annotated[str, Field(alias="POSTGRES_DB")]
    postgres_host: Annotated[str, Field(alias="POSTGRES_HOST")]
    postgres_port: Annotated[int, Field(alias="POSTGRES_PORT")]

    django_host: Annotated[str, Field(alias="DJANGO_SERVER_HOST")]
    django_port: Annotated[int, Field(alias="DJANGO_SERVER_PORT")]
    django_secret_key: Annotated[str, Field(alias="DJANGO_SECRET_KEY", min_length=32)]

    gunicorn_reload: bool
    gunicorn_workers_count: int

    redis_host: Annotated[str, Field(alias="REDIS_SERVER_HOST")]
    redis_port: Annotated[int, Field(alias="REDIS_PORT")]
    redis_password: Annotated[str, Field(alias="REDIS_PASSWORD")]

    fluent_bit_host: Annotated[str, Field(alias="FLUENT_BIT_HOST")]
    fluent_bit_port: Annotated[int, Field(alias="FLUENT_BIT_PORT")]

    # Vector search embeddings, served by the dedicated sentence-transformers container
    # (metax-embeddings). The model itself is fixed in embeddings_server/app.py; the app only
    # needs the host. EMBEDDING_DIM must match the served model (1024 for the Armenian E5 model).
    embedding_host: Annotated[str, Field(alias="EMBEDDING_HOST")] = "http://localhost:8082"
    embedding_dim: Annotated[int, Field(alias="EMBEDDING_DIM")] = 1024
    embedding_concurrency: Annotated[int, Field(alias="EMBEDDING_CONCURRENCY")] = 6
    # Generous enough to absorb a cold model load (the service downloads/loads the model on
    # first boot) plus a batch of embeddings under concurrent load.
    embedding_timeout: Annotated[float, Field(alias="EMBEDDING_TIMEOUT")] = 120.0

    # Embedding-based product category classification during crawling (no LLM); always on.
    # Max cosine distance (0=identical, 2=opposite) between a product and a category for the
    # product to be assigned that category. Lower = stricter. With curated example prototypes a
    # true match sits near 0, so this gate mainly rejects borderline guesses. Tune against real data.
    category_match_max_distance: Annotated[float, Field(alias="CATEGORY_MATCH_MAX_DISTANCE")] = 0.40

    # Whether to embed newly collected products (for search) right after a crawl. On by default;
    # set false to make a crawl just load raw data into the DB fast — embed later on demand with
    # scripts/backfill_embeddings.py. Note: search returns nothing for products with no embedding.
    embed_after_collect: Annotated[bool, Field(alias="EMBED_AFTER_COLLECT")] = True

    # A single global lock serializes the whole collect → embed → publish lifecycle across every
    # crawl job (nightly all-retailers + manual single-retailer). This is the max time it may be held
    # before Redis auto-expires it — a safety net so a crashed job can't wedge collection forever. It
    # must comfortably exceed the longest real run (a full crawl + embedding is minutes), hence 1h.
    collection_lock_ttl_seconds: Annotated[int, Field(alias="COLLECTION_LOCK_TTL_SECONDS")] = 3600

    telegram_bot_token: Annotated[str | None, Field(alias="TELEGRAM_BOT_TOKEN")] = None

    # By default, no .env file is read. Subclasses opt in explicitly.
    model_config = SettingsConfigDict(env_file=None, extra="ignore", env_ignore_empty=True)

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"

    @property
    def django_dir(self) -> str:
        return str(Path(self.project_root_pythonpath) / "metax/frameworks_and_drivers/django_framework")

    @property
    def project_root_pythonpath(self) -> str:
        project_root = Path(__file__).resolve().parent
        return str(project_root)


class DevConfigs(BaseConfigs):
    """Local development on the host.

    Values must stay in sync with ``docker-compose.dev.yml``. ``.env`` is NOT
    consulted - the class defaults below are the single source of truth for dev.
    """

    debug: bool = True

    postgres_host: str = "localhost"
    postgres_user: str = "p_user"
    postgres_password: str = "pass111"  # noqa: S105
    postgres_db: str = "metax"
    postgres_port: int = 5432

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "R_Super_Secret_Pass_2026!"  # noqa: S105

    django_host: str = "127.0.0.1"
    django_port: int = 8000
    django_secret_key: str = "django-dev-only-not-for-production-0123456789abcdef"  # noqa: S105

    gunicorn_reload: bool = False
    gunicorn_workers_count: int = 2

    fluent_bit_host: str = "mock"
    fluent_bit_port: int = 0

    embedding_host: str = "http://localhost:8082"

    model_config = SettingsConfigDict(env_file=None, extra="ignore", env_ignore_empty=True)


class TestConfigs(BaseConfigs):
    """CI / test configuration.

    Defaults below must mirror the hardcoded values in ``docker-compose.test.yml``
    (``x-metax-env`` block). In the containerized test stack Pydantic reads
    everything from ``os.environ`` (compose sets it), so these defaults are
    effectively a safety net for unit tests that instantiate the config without
    Docker.
    """

    debug: bool = False

    postgres_host: str = "metax-postgres-db"
    postgres_user: str = "p_user_test"
    postgres_password: str = "pass_test_111"  # noqa: S105
    postgres_db: str = "metax_test"
    postgres_port: int = 5432

    redis_host: str = "metax-redis"
    redis_port: int = 6379
    redis_password: str = "R_Test_Secret_2026!"  # noqa: S105

    django_host: str = "0.0.0.0"  # noqa: S104
    django_port: int = 8000
    django_secret_key: str = "django-ci-test-key-not-for-production-0123456789abcdef"  # noqa: S105

    gunicorn_reload: bool = False
    gunicorn_workers_count: int = 2

    fluent_bit_host: str = "metax-fluent-bit"
    fluent_bit_port: int = 24224

    embedding_host: str = "http://metax-embeddings:80"

    model_config = SettingsConfigDict(env_file=None, extra="ignore", env_ignore_empty=True)


class ProdConfigs(BaseConfigs):
    """Production configuration.

    Reads values exclusively from ``os.environ``. The container's environment is
    populated by ``docker-compose.prod.yml`` (which in turn interpolates secrets
    from the host ``.env`` via ``${VAR}`` at compose parse time). No defaults
    for app-level values — any missing variable triggers a Pydantic
    ``ValidationError`` at startup, by design.
    """

    debug: bool = False
    gunicorn_reload: bool = False
    gunicorn_workers_count: int = (multiprocessing.cpu_count() * 2) + 1

    model_config = SettingsConfigDict(env_file=None, extra="ignore", env_ignore_empty=True)


def _read_env_name_from_dotenv() -> str | None:
    """Peek at ``.env`` for ``ENV`` without polluting ``os.environ``.

    Allows ``ENV=dev`` in ``.env`` to drive environment selection while keeping
    ``DevConfigs`` independent of any other ``.env`` values.

    Returns:
        The value of ``ENV`` defined in ``.env``, or ``None`` if the file does
        not exist or does not declare ``ENV``.
    """
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        return None
    from dotenv import dotenv_values

    return dotenv_values(str(env_file)).get("ENV")


def configuration_factory() -> BaseConfigs:
    env_name = os.getenv("ENV") or _read_env_name_from_dotenv()

    match env_name:
        case "dev":
            return DevConfigs()
        case "test":
            return TestConfigs()
        case "prod":
            return ProdConfigs()
        case _:
            msg = f"Invalid ENV: {env_name!r}. Expected one of: 'dev', 'test', 'prod'."
            raise RuntimeError(msg)
