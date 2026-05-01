from constants import ErrorCodes
from metax_main_error import MetaxError


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
