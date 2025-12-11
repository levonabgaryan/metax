from backend.main_error import MainError

from .error_codes import CategoryErrorCodes


class DuplicateCategoryHelperWordsError(MainError):
    def __init__(self, duplicate_words: frozenset[str]) -> None:
        msg = f"Cannot add duplicate helper words: {', '.join(duplicate_words)}."
        super().__init__(message=msg, error_code=CategoryErrorCodes.DUPLICATE_HELPER_WORDS)


class CategoryHelperWordsNotFoundForDeletionError(MainError):
    def __init__(self, requested_words: frozenset[str]):
        msg = f"None of the requested words for deletion ({', '.join(requested_words)}) were found in the existing list."
        super().__init__(message=msg, error_code=CategoryErrorCodes.WORDS_NOT_FOUND_FOR_DELETION)
