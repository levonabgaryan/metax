from metax_main_error import MetaxError
from .error_codes import DiscountedProductsCollectorServiceErrorCodes


class RetailerNameIsMissing(MetaxError):
    def __init__(
        self,
        service_class_name: str,
        error_code: str = DiscountedProductsCollectorServiceErrorCodes.RETAILER_NAME_IS_MISSING,
    ) -> None:
        message = f"Retailer name in {service_class_name} missed."
        super().__init__(message=message, error_code=error_code)
