from abc import ABC, abstractmethod

from metax.core.application.read_models.discounted_product import (
    DiscountedProductReadModel,
)

# One page of results plus the total match count across all pages (for pagination).
type ReadModelPage = tuple[list[DiscountedProductReadModel], int]


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
        retailer_uuid: str | None = None,
        category_uuid: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ReadModelPage:
        """Rank products by relevance to ``name`` (lexical matches first, then semantic neighbours).

        ``retailer_uuid`` / ``category_uuid`` optionally narrow the results; they can be combined.

        Returns:
            One page of matches and the total number of matches across all pages.
        """

    @abstractmethod
    async def search_by_category_uuid(
        self,
        category_uuid: str,
        *,
        retailer_uuid: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ReadModelPage:
        """Browse a category, most confidently classified products first.

        ``retailer_uuid`` optionally narrows the browse to a single store.

        Returns:
            One page of the category's products and the category's total product count.
        """

    @abstractmethod
    async def search_by_retailer_uuid(
        self,
        retailer_uuid: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> ReadModelPage:
        """Browse one store's discounts, biggest discount (percent) first.

        Returns:
            One page of the store's products and the store's total product count.
        """

    @abstractmethod
    async def get_by_uuid(self, uuid_: str) -> DiscountedProductReadModel:
        pass
