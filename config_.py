import multiprocessing
import os
import sys
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
    opensearch_verify_certs: Annotated[bool, Field(alias="OPENSEARCH_VERIFY_CERTS")]

    django_host: Annotated[str, Field(alias="DJANGO_SERVER_HOST")]
    django_port: Annotated[int, Field(alias="DJANGO_SERVER_PORT")]
    django_secret_key: Annotated[str, Field(alias="DJANGO_SECRET_KEY")]

    gunicorn_reload: bool
    gunicorn_workers_count: int

    redis_host: Annotated[str, Field(alias="REDIS_SERVER_HOST")]
    redis_port: Annotated[int, Field(alias="REDIS_PORT")]
    redis_password: Annotated[str, Field(alias="REDIS_PASSWORD")]

    fluent_bit_host: Annotated[str, Field(alias="FLUENT_BIT_HOST")]
    fluent_bit_port: Annotated[int, Field(alias="FLUENT_BIT_PORT")]

    yerevan_city_data_source_url: Annotated[str, Field(alias="YEREVAN_CITY_DATA_SOURCE_URL")]
    yerevan_city_products_details_url: Annotated[str, Field(alias="YEREVAN_CITY_PRODUCTS_DETAILS_URL")]

    sas_am_main_page_url: Annotated[str, Field(alias="SAS_AM_MAIN_PAGE_URL")]
    sas_am_data_source_url: Annotated[str, Field(alias="SAS_AM_DATA_SOURCE_URL")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    @property
    def project_root_pythonpath(self) -> str:
        project_root = Path(__file__).resolve().parent
        return str(project_root)

    @property
    def django_dir(self) -> str:
        return str(Path(self.project_root_pythonpath) / "metax/frameworks_and_drivers/django_framework")

    @property
    def celery_broker_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    @property
    def celery_result_backend_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/1"


class DevConfigs(BaseConfigs):
    # When you run locally, make sure that variables from env are same here
    debug: bool = True

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "p_user"
    postgres_password: str = "pass111"  # noqa: S105
    postgres_db: str = "discount-system"

    opensearch_host: str = "localhost"
    opensearch_verify_certs: bool = False

    django_secret_key: str = "django-insecure-bp^ztjw1urwqz4+=(+!k=k^zzdz8c2+qwr7z1_!1mo-%j5^)0s"  # noqa: S105

    # Local dev uses uvicorn --reload (run_metax); gunicorn reload is off here.
    gunicorn_reload: bool = False
    gunicorn_workers_count: int = 1

    redis_port: int = 6379
    redis_password: str = "R_Super_Secret_Pass_2026!"  # noqa: S105

    fluent_bit_host: str = "mock"
    fluent_bit_port: int = 0

    opensearch_user: str = "admin"
    opensearch_password: str = "Os_Super_Secret_Pass_2026!"  # noqa: S105
    opensearch_port: int = 9200

    django_host: str = "localhost"
    django_port: int = 8000
    redis_host: str = "localhost"


class TestConfigs(BaseConfigs):
    debug: bool = True

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "p_user"
    postgres_password: str = "pass111"  # noqa: S105
    postgres_db: str = "metax"

    opensearch_host: str = "localhost"
    opensearch_verify_certs: bool = False

    django_secret_key: str = "django-insecure-bp^ztjw1urwqz4+=(+!k=k^zzdz8c2+qwr7z1_!1mo-%j5^)0s"  # noqa: S105

    gunicorn_reload: bool = False
    gunicorn_workers_count: int = 1

    redis_port: int = 6379
    redis_password: str = "R_Super_Secret_Pass_2026!"  # noqa: S105

    fluent_bit_host: str = "mock"
    fluent_bit_port: int = 0

    opensearch_user: str = "admin"
    opensearch_password: str = "Os_Super_Secret_Pass_2026!"  # noqa: S105
    opensearch_port: int = 9200

    django_host: str = "localhost"
    django_port: int = 8000
    redis_host: str = "localhost"

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        env_prefix="TEST_FORCE_IGNORE_",
    )


class ProdConfigs(BaseConfigs):
    debug: bool = False
    gunicorn_reload: bool = False
    gunicorn_workers_count: int = (multiprocessing.cpu_count() * 2) + 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=False)


def configuration_factory() -> BaseConfigs:
    from dotenv import load_dotenv

    load_dotenv()
    env_name = os.getenv("ENV")

    if "pytest" in sys.modules or "pytest" in sys.argv[0]:
        env_name = "test"

    match env_name:
        case "dev":
            return DevConfigs()
        case "test":
            return TestConfigs()
        case "prod":
            return ProdConfigs()
        case _:
            msg = f"Invalid ENV: {env_name}"
            raise RuntimeError(msg)


metax_configs = configuration_factory()
