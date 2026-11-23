from constants import ErrorCodes
from metax_error import MetaxError


class NoRetailersError(MetaxError):
    """Raised when retailer_repo has no rows to process."""

    def __init__(self) -> None:
        title = "No retailers to collect discounted products for."
        details = "Retailer repository returned no rows."
        super().__init__(
            title=title,
            error_code=ErrorCodes.NO_RETAILERS,
            details=details,
        )


class NothingCollectedError(MetaxError):
    """Raised when a retailer's collector finishes without a single product.

    Collectors swallow request errors (a down or blocking site ends the crawl quietly), so "0 products"
    almost always means the crawl broke, not that the store has no discounts. Raising turns it into a
    regular crawler failure: the retailer's existing rows are not deleted and the digest reports it.
    """

    def __init__(self, retailer_name: str) -> None:
        super().__init__(
            title="Collector returned no products.",
            error_code=ErrorCodes.NOTHING_COLLECTED,
            details=f"Collector for retailer {retailer_name!r} finished with 0 products.",
        )
