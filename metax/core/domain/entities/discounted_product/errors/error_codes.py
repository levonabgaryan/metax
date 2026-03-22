from enum import StrEnum


class DiscountedProductErrorCodes(StrEnum):
    NEGATIVE_PRICE = "NEGATIVE_PRICE"
    DISCOUNT_EXCEEDS_PRICE = "DISCOUNT_EXCEEDS_PRICE"
