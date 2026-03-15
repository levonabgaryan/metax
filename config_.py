import os
from functools import lru_cache
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
        return str(Path(self.project_root_pythonpath) / "discount_service/frameworks_and_drivers/django_framework")

    @property
    def celery_broker_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    @property
    def celery_result_backend_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/1"


class DevConfigs(BaseConfigs):
    # When you run locally, make sure that variables from env are same here
    debug: bool = True

    postgres_user: Annotated[str, Field(default="p_user")]
    postgres_password: Annotated[str, Field(default="pass111")]
    postgres_db: Annotated[str, Field(default="discount-system")]
    postgres_host: Annotated[str, Field(default="localhost")]
    postgres_port: Annotated[int, Field(default="5432")]

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

    redis_host: Annotated[str, Field(default="localhost")]
    redis_port: Annotated[int, Field(default=6379)]
    redis_password: Annotated[str, Field(default="My_Super_Secret_Pass_2026!")]


class TestConfigs(BaseConfigs):
    debug: bool = True

    postgres_user: Annotated[str, Field(default="p_user")]
    postgres_password: Annotated[str, Field(default="pass111")]
    postgres_db: Annotated[str, Field(default="discount-system")]
    postgres_host: Annotated[str, Field(default="localhost")]
    postgres_port: Annotated[int, Field(default="5432")]

    opensearch_user: Annotated[str, Field(default="admin")]
    opensearch_password: Annotated[str, Field(default="My_Super_Secret_Pass_2026!")]
    opensearch_host: Annotated[str, Field(default="localhost")]
    opensearch_port: Annotated[int, Field(default=9200)]
    opensearch_verify_certs: Annotated[bool, Field(default=False)]

    django_host: Annotated[str, Field(default="0.0.0.0")]
    django_port: Annotated[int, Field(default=8000)]
    django_secret_key: Annotated[
        str, Field(default="django-insecure-bp^ztjw1urwqz4+=(+!k=k^zzdz8c2+qwr7z1_!1mo-%j5^)0s")
    ]

    yerevan_city_products_details_url: Annotated[str, Field(default="mock")]
    yerevan_city_discount_page_url: Annotated[str, Field(default="mock")]

    sas_am_main_page_url: Annotated[str, Field(default="mock")]
    sas_am_data_source_url: Annotated[str, Field(default="mock")]


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

# Logging advices

# STDIN (Standard Input):
# Данные в stdin могут «вливаться» из другого файла или даже из вывода другой программы через символ конвейера (|). Например: cat data.txt | python script.py.
#
# STDOUT (Standard Output):
# Нюанс: Важно помнить, что stdout буферизуется. Это значит, что данные могут не появиться на экране мгновенно, а копиться в памяти, пока их не станет достаточно много для вывода (или пока ты не вызовешь flush).
#
# STDERR (Standard Error):
# Нюанс: Главная фишка в том, что stderr обычно не буферизуется. Ошибка должна «вылететь» на экран немедленно, как только она произошла, не дожидаясь наполнения буфера.
