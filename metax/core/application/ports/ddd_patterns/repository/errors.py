from typing import Any

from metax_main_error import MetaxError


class EntityIsNotFoundError(MetaxError):
    def __init__(
        self,
        entity_type: str,
        searched_field_name: str,
        searched_field_value: str,
    ) -> None:
        message = (
            f"There is no {entity_type} entity found "
            f"by field '{searched_field_name}' with value '{searched_field_value}'."
        )

        super().__init__(title=message, error_code="ENTITY_IS_NOT_FOUND")


class EntityAlreadyExistsError(MetaxError):
    def __init__(self, entity_type: str, entity_field_value: Any, entity_field_name: str) -> None:
        msg = f"There is already a(n) {entity_type} entity found by field '{entity_field_name}' with value '{entity_field_value}'."  # noqa: E501
        super().__init__(title=msg, error_code="ENTITY_ALREADY_CREATED")
