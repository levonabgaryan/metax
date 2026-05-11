from __future__ import annotations

from enum import StrEnum


class RetailersNames(StrEnum):
    YEREVAN_CITY = "yerevan-city"
    SAS_AM = "sas-am"


def parse_retailer_name(name: str) -> RetailersNames:
    try:
        return RetailersNames(name)
    except ValueError as exc:
        from metax.core.domain.entities.retailer.errors import InvalidRetailerNameError

        raise InvalidRetailerNameError(name) from exc
