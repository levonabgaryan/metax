from metax_main_error import MetaxError


class EntityIsNotFoundError(MetaxError):
    def __init__(
        self, entity_name: str, searched_field_name: str, searched_field_value: str, error_code: str
    ) -> None:
        message = (
            f"There is no {entity_name} entity found "
            f"by field '{searched_field_name}' with value '{searched_field_value}'."
        )  # Output: There is no Category entity found by field 'name' with value 'alcohol12'.

        super().__init__(title=message, error_code=error_code)
