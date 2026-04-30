type DbFieldName = str
type DbFieldValue = str


def extract_field_from_integrity_message(msg: str) -> tuple[DbFieldName, DbFieldValue]:
    """Extract field name and value from IntegrityError message.

    Example:
        msg = DETAIL:  Key (name)=(Electronics) already exists.
        extract_field = extract_field_from_integrity_message(cause_)
        extract_field -> (name, Electronics)

    Returns:
        Field name and field value from IntegrityError message
    """
    first_open = msg.find("(")
    first_close = msg.find(")", first_open + 1)
    second_open = msg.find("(", first_close + 1)
    second_close = msg.find(")", second_open + 1)

    field_name = msg[first_open + 1 : first_close]
    field_value = msg[second_open + 1 : second_close]
    return field_name, field_value
