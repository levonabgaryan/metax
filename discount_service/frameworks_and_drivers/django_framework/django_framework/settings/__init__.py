import os
import sys
from split_settings.tools import include
from dotenv import find_dotenv, load_dotenv


class DjangoSettingsError(Exception):
    """Raised when the project configuration is invalid."""

    pass


load_dotenv(find_dotenv(filename=".env"))

is_testing = (
    "test" in sys.argv
    or "pytest" in sys.modules
    or any("pytest" in arg for arg in sys.argv)
    or any("test" in arg for arg in sys.argv)
)

if is_testing:
    ENV = "test"
    os.environ["ENV"] = "test"
else:
    ENV = os.getenv("ENV", "dev")

include("base.py")

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
