from constants import ErrorCodes
from metax.core.domain.entities.retailer.value_objects import RetailersNames
from metax_main_error import MetaxError


class InvalidRetailerNameError(MetaxError):
    def __init__(self, name: str) -> None:
        allowed = ", ".join(sorted(m.value for m in RetailersNames))
        super().__init__(
            title="Invalid retailer name.",
            details=f"Received {name!r}. Allowed slugs: {allowed}.",
            error_code=ErrorCodes.INVALID_RETAILER_NAME,
        )
