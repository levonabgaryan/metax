from uuid import UUID

from backend.core.domain.ddd_patterns import AggregateRootEntity


class Retailer(AggregateRootEntity):
    def __init__(
        self,
        retailer_uuid: UUID,
        name: str,
        url: str,
        phone_number: str,
    ) -> None:
        super().__init__(_uuid=retailer_uuid)
        self.__name = name
        self.__url = url
        self.__phone_number = phone_number
