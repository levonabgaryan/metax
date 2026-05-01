from constants import ErrorCodes
from metax_main_error import MetaxError


class DuplicateCategoryHelperWordsError(MetaxError):
    def __init__(self, duplicate_helper_words: frozenset[str]) -> None:
        title = "Cannot add duplicate helper words."
        details = f"Duplicate words: {', '.join(sorted(duplicate_helper_words))}."
        super().__init__(title=title, error_code=ErrorCodes.DUPLICATE_HELPER_WORDS, details=details)


class CategoryHelperWordsNotFoundForDeletionError(MetaxError):
    def __init__(self, requested_words: frozenset[str]):
        title = "Some helper words were not found in category."
        details = f"Requested words not found: {', '.join(sorted(requested_words))}."
        super().__init__(title=title, error_code=ErrorCodes.WORDS_NOT_FOUND_FOR_DELETION, details=details)
