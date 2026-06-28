from abc import ABC, abstractmethod

from metax.core.application.read_models.discounted_product import (
    DiscountedProductReadModel,
)


class DiscountedProductReadModelRepository(ABC):
    """Read side of search (CQRS): queries the ``discounted_products`` table directly.

    Since search now lives in the same Postgres database as the write model, there is no
    separate read store to keep in sync — retailer/category data is read live via joins. The
    only write-side concern here is keeping the ``name_embedding`` vector populated, which
    ``embed_pending`` handles after each crawl.
    """

    @abstractmethod
    async def embed_pending(self, batch_size: int = 500) -> int:
        """Compute and store embeddings for products that don't have one yet.

        Returns:
            The number of products embedded.
        """

    @abstractmethod
    async def count_pending(self) -> int:
        """Return how many products still have no ``name_embedding`` (NULL).

        Returns:
            The number of products awaiting an embedding.
        """

    @abstractmethod
    async def search_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        pass

    @abstractmethod
    async def search_by_name_and_by_retailer_uuid(
        self,
        name: str,
        retailer_uuid: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        pass

    @abstractmethod
    async def search_by_name_and_by_category_uuid(
        self,
        name: str,
        category_uuid: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        pass

    @abstractmethod
    async def search_by_category_uuid(
        self,
        category_uuid: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        """Return all products in a category, sorted by discounted price ascending."""

    @abstractmethod
    async def get_by_uuid(self, uuid_: str) -> DiscountedProductReadModel:
        pass
