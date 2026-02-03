import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class BaseConfigs(BaseSettings):
    sqlite_db_name: Annotated[str, Field(alias="SQLITE_DB_NAME")]

    opensearch_user: Annotated[str, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_USER")]
    opensearch_password: Annotated[str, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_INITIAL_ADMIN_PASSWORD")]
    opensearch_host: Annotated[str, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_NODE_HOST")]
    opensearch_port: Annotated[int, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_NODE_PORT")]
    opensearch_verify_certs: Annotated[bool, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_VERIFY_CERTS")]

    django_host: Annotated[str, Field(alias="DJANGO_SERVER_HOST")]
    django_port: Annotated[int, Field(alias="DJANGO_SERVER_PORT")]
    django_secret_key: Annotated[str, Field(alias="DJANGO_SECRET_KEY")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    @property
    def project_root_pythonpath(self) -> str:
        project_root = Path(__file__).resolve().parent
        return str(project_root)

    @property
    def django_dir(self) -> str:
        return str(Path(self.project_root_pythonpath) / "discount_service/frameworks_and_drivers/django_framework")


class DevConfigs(BaseConfigs):
    # When you run locally, make sure that variables from env are same here
    debug: Annotated[bool, Field(default=True)]

    sqlite_db_name: Annotated[str, Field(default="db_for_dev")]

    opensearch_user: Annotated[str, Field(default="admin")]
    opensearch_password: Annotated[str, Field(default="My_Super_Secret_Pass_2026!")]
    opensearch_host: Annotated[str, Field(default="localhost")]
    opensearch_port: Annotated[int, Field(default=9200)]
    opensearch_verify_certs: Annotated[bool, Field(default=False)]

    django_host: Annotated[str, Field(default="localhost")]
    django_port: Annotated[int, Field(default=8000)]
    django_secret_key: Annotated[
        str, Field(default="django-insecure-bp^ztjw1urwqz4+=(+!k=k^zzdz8c2+qwr7z1_!1mo-%j5^)0s")
    ]


class TestConfigs(BaseConfigs):
    debug: Annotated[bool, Field(default=False)]

    sqlite_db_name: Annotated[str, Field(default="db_for_test")]

    opensearch_user: Annotated[str, Field(default="admin")]
    opensearch_password: Annotated[str, Field(default="My_Super_Secret_Pass_2026!")]
    opensearch_host: Annotated[str, Field(default="localhost")]
    opensearch_port: Annotated[int, Field(default=9200)]
    opensearch_verify_certs: Annotated[bool, Field(default=False)]

    django_host: Annotated[str, Field(default="localhost")]
    django_port: Annotated[int, Field(default=8000)]
    django_secret_key: Annotated[
        str, Field(default="django-insecure-bp^ztjw1urwqz4+=(+!k=k^zzdz8c2+qwr7z1_!1mo-%j5^)0s")
    ]


class ProdConfigs(BaseConfigs):
    debug: Annotated[bool, Field(default=False)]


@lru_cache
def get_configs() -> BaseConfigs:
    from dotenv import load_dotenv

    load_dotenv()
    env_name = os.getenv("ENV")

    match env_name:
        case "dev":
            return DevConfigs()
        case "test":
            return TestConfigs()
        case "prod":
            return ProdConfigs()
        case _:
            raise RuntimeError(f"Invalid ENV: {env_name}")


discount_service_configs = get_configs()
