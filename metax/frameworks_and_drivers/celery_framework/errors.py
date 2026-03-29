from metax_main_error import MetaxError


class NoRetailersError(MetaxError):
    """Raised when retailer_repo has no rows to process."""

    def __init__(self) -> None:
        super().__init__("No retailers")
