from typing import Callable
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

    def set_name(self, new_name: str) -> None:
        self.__name = new_name

    def set_url(self, new_url: str) -> None:
        self.__url = new_url

    def set_phone_number(self, new_phone_number: str) -> None:
        self.__phone_number = new_phone_number

    def get_name(self) -> str:
        return self.__name

    def get_url(self) -> str:
        return self.__url

    def get_phone_number(self) -> str:
        return self.__phone_number

    def update(self, new_data: dict[str, str]) -> None:
        dispatch_map: dict[str, Callable[[str], None]] = {
            "new_name": self.set_name,
            "new_url": self.set_url,
            "new_phone_number": self.set_phone_number,
        }
        for key, value in new_data.items():
            handler: Callable[[str], None] | None = dispatch_map.get(key)
            if handler:
                handler(value)
