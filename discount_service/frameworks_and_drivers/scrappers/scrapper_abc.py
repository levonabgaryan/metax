from abc import ABC, abstractmethod
from typing import AsyncIterator, TypedDict, TypeVar


class ScrapperBaseDTO(TypedDict):
    pass


GenericScrapperDTO = TypeVar("GenericScrapperDTO", bound=ScrapperBaseDTO)


class ScrapperAdapter[GenericScrapperDTO](ABC):
    def __init__(self, scrapper_url: str) -> None:
        self._scrapper_url = scrapper_url

    @abstractmethod
    def fetch(self) -> AsyncIterator[GenericScrapperDTO]:
        pass
