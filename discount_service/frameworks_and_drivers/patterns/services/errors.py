from main_error import MainError
from .error_codes import DiscountedProductsCollectorServiceErrorCodes


class RetailerNameIsMissing(MainError):
    def __init__(
        self,
        service_class_name: str,
        error_code: str = DiscountedProductsCollectorServiceErrorCodes.RETAILER_NAME_IS_MISSING,
    ) -> None:
        message = f"Retailer name in {service_class_name} missed."
        super().__init__(message=message, error_code=error_code)
