"""Application configuration.

Three environments are supported, selected via the ``ENV`` environment variable:

* ``dev``  - run the metax application on the host (outside Docker). Database
             containers are spun up via ``fluent-bit-compose.dev.yml``.
             ``DevConfigs`` does NOT read any ``.env`` file: all values are the
             class-level defaults below and they must stay in sync with
             ``fluent-bit-compose.dev.yml``.
* ``test`` - CI / integration tests. The whole stack runs in Docker via
             ``fluent-bit-compose.test.yml`` and all values are passed in by Compose
             as container environment variables. ``TestConfigs`` provides
             defaults that match ``fluent-bit-compose.test.yml``.
* ``prod`` - production. The whole stack runs in Docker via
             ``fluent-bit-compose.prod.yml``. ``ProdConfigs`` reads ``.env``
             (mounted/created at deploy time) and has no defaults for secrets.
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

    opensearch_user: Annotated[str, Field(alias="OPENSEARCH_USERNAME")]
    opensearch_password: Annotated[str, Field(alias="OPENSEARCH_ADMIN_PASSWORD")]
    opensearch_host: Annotated[str, Field(alias="OPENSEARCH_HOST")]
    opensearch_port: Annotated[int, Field(alias="OPENSEARCH_NODE_PORT")]
    opensearch_verify_certs: bool = False

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

    Values must stay in sync with ``fluent-bit-compose.dev.yml``. ``.env`` is NOT
    consulted - the class defaults below are the single source of truth for dev.
    """

    debug: bool = True

    postgres_host: str = "localhost"
    postgres_user: str = "p_user"
    postgres_password: str = "pass111"  # noqa: S105
    postgres_db: str = "metax"
    postgres_port: int = 5432

    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_user: str = "admin"
    opensearch_password: str = "Os_Super_Secret_Pass_2026!"  # noqa: S105

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

    model_config = SettingsConfigDict(env_file=None, extra="ignore", env_ignore_empty=True)


class TestConfigs(BaseConfigs):
    """CI / test configuration.

    Defaults match the values hardcoded in ``fluent-bit-compose.test.yml``. When
    the metax container starts inside the Compose network, those values are
    re-set as container env vars and Pydantic picks them up from ``os.environ``.
    """

    debug: bool = False

    postgres_host: str = "metax-postgres-db"
    postgres_user: str = "p_user_test"
    postgres_password: str = "pass_test_111"  # noqa: S105
    postgres_db: str = "metax_test"
    postgres_port: int = 5432

    opensearch_host: str = "metax-opensearch-db"
    opensearch_port: int = 9200
    opensearch_user: str = "admin"
    opensearch_password: str = "Os_Test_Secret_2026!"  # noqa: S105

    redis_host: str = "metax-redis"
    redis_port: int = 6379
    redis_password: str = "R_Test_Secret_2026!"  # noqa: S105

    django_host: str = "0.0.0.0"  # noqa: S104
    django_port: int = 8000
    django_secret_key: str = "django-ci-test-key-not-for-production-0123456789abcdef"  # noqa: S105

    gunicorn_reload: bool = False
    gunicorn_workers_count: int = 1

    fluent_bit_host: str = "metax-fluent-bit"
    fluent_bit_port: int = 24224

    model_config = SettingsConfigDict(env_file=None, extra="ignore", env_ignore_empty=True)


class ProdConfigs(BaseConfigs):
    """Production configuration.

    Reads values exclusively from environment / ``.env``. No defaults for
    secrets - the application will fail loudly at startup if anything required
    is missing.
    """

    debug: bool = False
    gunicorn_reload: bool = False
    gunicorn_workers_count: int = (multiprocessing.cpu_count() * 2) + 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)


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
