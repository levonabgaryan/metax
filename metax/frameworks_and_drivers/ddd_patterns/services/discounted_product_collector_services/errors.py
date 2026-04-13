from metax_main_error import MetaxError

from .error_codes import DiscountedProductStrategyErrorCodes


class InvalidUrlForScrappingError(MetaxError):
    def __init__(self, invalid_url: str) -> None:
        super().__init__(
            error_code=DiscountedProductStrategyErrorCodes.INVALID_URL_FOR_SCRAPING,
            title=f"Invalid URL for scraping: {invalid_url}",
        )
