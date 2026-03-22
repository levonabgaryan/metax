from metax_main_error import MetaxError

from .error_codes import CategoryErrorCodes


class DuplicateCategoryHelperWordsError(MetaxError):
    def __init__(self, duplicate_words: frozenset[str]) -> None:
        msg = f"Cannot add duplicate helper words: {', '.join(sorted(duplicate_words))}."
        super().__init__(message=msg, error_code=CategoryErrorCodes.DUPLICATE_HELPER_WORDS)


class CategoryHelperWordsNotFoundForDeletionError(MetaxError):
    def __init__(self, requested_words: frozenset[str]):
        msg = f"None of the requested words for deletion ({', '.join(sorted(requested_words))}) were found in the existing list."
        super().__init__(message=msg, error_code=CategoryErrorCodes.WORDS_NOT_FOUND_FOR_DELETION)
