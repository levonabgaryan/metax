from abc import ABC, abstractmethod

from metax.core.domain.entities.category.aggregate_root_entity import Category
from metax.core.domain.entities.discounted_product.aggregate_root_entity import DiscountedProduct


class CategoryClassifierService(ABC):
    """Assigns a category to freshly collected products during a crawl."""

    @abstractmethod
    async def classify_products(
        self,
        products: list[DiscountedProduct],
        categories: list[Category],
    ) -> None:
        """Mutate ``products`` in-place, setting ``category_uuid`` where a category matches.

        Products that do not match any category confidently are left untouched (no category).
        """
