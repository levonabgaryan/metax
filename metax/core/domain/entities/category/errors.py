from metax_main_error import MetaxError


class DuplicateCategoryHelperWordsError(MetaxError):
    def __init__(self, duplicate_helper_words: frozenset[str]) -> None:
        msg = f"Cannot add duplicate helper words: {', '.join(sorted(duplicate_helper_words))}."
        super().__init__(title=msg, error_code="DUPLICATE_HELPER_WORDS")


class CategoryHelperWordsNotFoundForDeletionError(MetaxError):
    def __init__(self, requested_words: frozenset[str]):
        msg = f"There are no any words in category by following: ({', '.join(sorted(requested_words))})."
        super().__init__(title=msg, error_code="WORDS_NOT_FOUND_FOR_DELETION")
