from main_error import MainError


class EntityIsNotFoundError(MainError):
    def __init__(
        self, entity_name: str, searched_field_name: str, searched_field_value: str, error_code: str
    ) -> None:
        message = (
            f"There is no {entity_name} entity found "
            f"by field '{searched_field_name}' with value '{searched_field_value}'."
        )  # Output: There is no Category entity found by field 'name' with value 'alcohol12'.

        details = {"searched_field_name": searched_field_name, "searched_field_value": searched_field_value}
        super().__init__(message=message, error_code=error_code, details=details)
