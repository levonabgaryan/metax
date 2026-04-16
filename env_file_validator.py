from dotenv import dotenv_values

from metax_main_error import MetaxError


def validate_env_structure() -> None:
    template = dotenv_values("env_template")
    actual = dotenv_values(".env")

    template_keys = set(template.keys())
    actual_keys = set(actual.keys())

    missing = template_keys - actual_keys

    if missing:
        raise MetaxError(
            error_code="ENV_VALIDATION_ERROR",
            title=f".env does not match to env_template. Missing variables: {missing}. \n",
        )
    print("✅ .env matches to env_template.")  # noqa: T201


if __name__ == "__main__":
    validate_env_structure()
