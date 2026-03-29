from metax_main_error import MetaxError

from .error_codes import CeleryFrameworkErrorCodes


class NoRetailersError(MetaxError):
    """Raised when retailer_repo has no rows to process."""

    def __init__(self) -> None:
        super().__init__(
            error_code=CeleryFrameworkErrorCodes.NO_RETAILERS,
            message="No retailers to collect discounted products for.",
        )
