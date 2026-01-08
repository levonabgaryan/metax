import os
from split_settings.tools import include
from dotenv import find_dotenv, load_dotenv


class DjangoSettingsError(Exception):
    """Raised when the project configuration is invalid."""

    pass


load_dotenv(find_dotenv(filename=".env"))

include("base.py")
ENV = os.getenv("ENV")

match ENV:
    case "dev":
        include("dev.py")
    case "prod":
        include("prod.py")
    case "test":
        include("test.py")
    case _:
        msg = """
            Environment variable 'ENV' is set incorrectly.
            Use one of the following: 'dev', 'prod', 'test'.
            """
        raise DjangoSettingsError(msg)
