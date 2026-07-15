from __future__ import annotations

from enum import StrEnum


class RetailersNames(StrEnum):
    YEREVAN_CITY = "yerevan-city"
    SAS_AM = "sas-am"
    TNTESAKAN_AM = "tntesakan-am"
    ROUGE_AM = "rouge-am"
    VLV_AM = "vlv-am"
    ZIGZAG_AM = "zigzag-am"


def parse_retailer_name(name: str) -> RetailersNames:
    try:
        return RetailersNames(name)
    except ValueError as exc:
        from metax.core.domain.entities.retailer.errors import InvalidRetailerNameError

        raise InvalidRetailerNameError(name) from exc
