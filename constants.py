from enum import StrEnum, auto


class ErrorCodes(StrEnum):
    METAX_ERROR = auto()
    DUPLICATE_HELPER_WORDS = auto()
    WORDS_NOT_FOUND_FOR_DELETION = auto()
    NEGATIVE_PRICE = auto()
    DISCOUNT_EXCEEDS_PRICE = auto()
    ENTITY_IS_NOT_FOUND = auto()
    ENTITY_ALREADY_EXISTS = auto()
    INVALID_UUID = auto()
    DATETIME_NOT_UTC = auto()
    UPDATE_BEFORE_CREATION = auto()
    INVALID_URL_FOR_SCRAPING = auto()
    NO_RETAILERS = auto()
