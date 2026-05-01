from typing import Any

from constants import ErrorCodes
from metax_main_error import MetaxError


class EntityIsNotFoundError(MetaxError):
    def __init__(
        self,
        entity_type: str,
        searched_field_name: str,
        searched_field_value: str,
    ) -> None:
        title = f"{entity_type} not found."
        details = f"No {entity_type} found by '{searched_field_name}' = '{searched_field_value}'."

        super().__init__(title=title, error_code=ErrorCodes.ENTITY_IS_NOT_FOUND, details=details)


class EntityAlreadyExistsError(MetaxError):
    def __init__(self, entity_type: str, entity_field_value: Any, entity_field_name: str) -> None:
        title = f"{entity_type} already exists."
        details = f"An existing {entity_type} was found by '{entity_field_name}' = '{entity_field_value}'."
        super().__init__(title=title, error_code=ErrorCodes.ENTITY_ALREADY_EXISTS, details=details)
