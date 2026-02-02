import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class BaseConfigs(BaseSettings):
    debug: bool = False

    sqlite_db_name: Annotated[str, Field(alias="SQLITE_DB_NAME")]

    opensearch_user: Annotated[str, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_USER")]
    opensearch_password: Annotated[str, Field(alias="OPENSEARCH_PASSWORD")]
    opensearch_host: Annotated[str, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_NODE_HOST")]
    opensearch_port: Annotated[int, Field(alias="DISCOUNT_SERVICE_OPENSEARCH_NODE_PORT")]
    opensearch_verify_certs: Annotated[bool, Field(alias="OPENSEARCH_VERIFY_CERTS")]

    django_host: Annotated[str, Field(alias="DJANGO_SERVER_HOST")]
    django_port: Annotated[int, Field(alias="DJANGO_SERVER_PORT")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    @property
    def project_root_pythonpath(self) -> str:
        project_root = Path(__file__).resolve().parent
        return str(project_root)

    @property
    def django_dir(self) -> str:
        return str(Path(self.project_root_pythonpath) / "discount_service/frameworks_and_drivers/django_framework")

    @field_validator("opensearch_verify_certs", mode="before")
    @classmethod
    def parse_bool(cls, v: bool | str) -> bool:
        if v == "":
            return False
        elif v in (True, False):
            return True
        elif isinstance(v, str):
            if v.lower() == "true":
                return True
            elif v.lower() == "false":
                return False
        raise ValueError(f"Invalid boolean value: {v}")


class DevConfigs(BaseConfigs):
    # When you run locally, make sure that variables from env are same here
    debug: bool = True
    sqlite_db_name: str = "db_for_dev.sqlite3"
    opensearch_user: str = "admin"
    opensearch_password: str = "My_Super_Secret_Pass_2026!"
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_verify_certs: bool = False
    django_host: str = "localhost"
    django_port: int = 8000


class TestConfigs(BaseConfigs):
    debug: bool = False


class ProdConfigs(BaseConfigs):
    debug: bool = False


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
