from constants import ErrorCodes
from metax_main_error import MetaxError


class InvalidUrlForScrappingError(MetaxError):
    def __init__(self, invalid_url: str) -> None:
        title = "Invalid URL for scraping."
        details = f"Received URL: {invalid_url}."
        super().__init__(error_code=ErrorCodes.INVALID_URL_FOR_SCRAPING, title=title, details=details)
