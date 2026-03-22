import os
import sys
from pathlib import Path
from typing import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


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

    redis_host: Annotated[str, Field(alias="REDIS_SERVER_HOST")]
    redis_port: Annotated[int, Field(alias="REDIS_PORT")]
    redis_password: Annotated[str, Field(alias="REDIS_PASSWORD")]

    fluent_bit_host: Annotated[str, Field(alias="FLUENT_BIT_HOST")]
    fluent_bit_port: Annotated[int, Field(alias="FLUENT_BIT_PORT")]

    yerevan_city_data_source_url: Annotated[str, Field(alias="YEREVAN_CITY_DATA_SOURCE_URL")]
    yerevan_city_products_details_url: Annotated[str, Field(alias="YEREVAN_CITY_PRODUCTS_DETAILS_URL")]
    yerevan_city_discount_page_url: Annotated[str, Field(alias="YEREVAN_CITY_DISCOUNT_PAGE_URL")]

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

    postgres_host: Annotated[str, Field(default="localhost")]
    postgres_port: Annotated[int, Field(default="5432")]
    postgres_user: Annotated[str, Field(default="p_user")]
    postgres_password: Annotated[str, Field(default="pass111")]
    postgres_db: Annotated[str, Field(default="discount-system")]

    opensearch_user: Annotated[str, Field(default="admin")]
    opensearch_password: Annotated[str, Field(default="Os_Super_Secret_Pass_2026!")]
    opensearch_host: Annotated[str, Field(default="localhost")]
    opensearch_port: Annotated[int, Field(default=9200)]
    opensearch_verify_certs: Annotated[bool, Field(default=False)]

    django_host: Annotated[str, Field(default="0.0.0.0")]
    django_port: Annotated[int, Field(default=8000)]
    django_secret_key: Annotated[
        str, Field(default="django-insecure-bp^ztjw1urwqz4+=(+!k=k^zzdz8c2+qwr7z1_!1mo-%j5^)0s")
    ]

    redis_host: Annotated[str, Field(default="localhost")]
    redis_port: Annotated[int, Field(default=6379)]
    redis_password: Annotated[str, Field(default="R_Super_Secret_Pass_2026!")]

    fluent_bit_host: Annotated[str, Field(default="mock")]
    fluent_bit_port: Annotated[int, Field(default=0)]

    yerevan_city_products_details_url: Annotated[str, Field(default="mock")]
    yerevan_city_discount_page_url: Annotated[str, Field(default="mock")]

    sas_am_main_page_url: Annotated[str, Field(default="mock")]
    sas_am_data_source_url: Annotated[str, Field(default="mock")]


class TestConfigs(BaseConfigs):
    debug: bool = True

    postgres_host: Annotated[str, Field(default="localhost")]
    postgres_port: Annotated[int, Field(default="5432")]
    postgres_user: Annotated[str, Field(default="p_user")]
    postgres_password: Annotated[str, Field(default="pass111")]
    postgres_db: Annotated[str, Field(default="metax")]

    opensearch_user: Annotated[str, Field(default="admin")]
    opensearch_password: Annotated[str, Field(default="Os_Super_Secret_Pass_2026!")]
    opensearch_host: Annotated[str, Field(default="localhost")]
    opensearch_port: Annotated[int, Field(default=9200)]
    opensearch_verify_certs: Annotated[bool, Field(default=False)]

    django_host: Annotated[str, Field(default="0.0.0.0")]
    django_port: Annotated[int, Field(default=8000)]
    django_secret_key: Annotated[
        str, Field(default="django-insecure-bp^ztjw1urwqz4+=(+!k=k^zzdz8c2+qwr7z1_!1mo-%j5^)0s")
    ]

    redis_host: Annotated[str, Field(default="localhost")]
    redis_port: Annotated[int, Field(default=6379)]
    redis_password: Annotated[str, Field(default="R_Super_Secret_Pass_2026!")]

    fluent_bit_host: Annotated[str, Field(default="mock")]
    fluent_bit_port: Annotated[int, Field(default=0)]

    yerevan_city_products_details_url: Annotated[str, Field(default="mock")]
    yerevan_city_discount_page_url: Annotated[str, Field(default="mock")]

    sas_am_main_page_url: Annotated[str, Field(default="mock")]
    sas_am_data_source_url: Annotated[str, Field(default="mock")]
    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        env_prefix="TEST_FORCE_IGNORE_",
    )


class ProdConfigs(BaseConfigs):
    debug: bool = False


def get_configs() -> BaseConfigs:
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
            raise RuntimeError(f"Invalid ENV: {env_name}")


metax_configs = get_configs()
