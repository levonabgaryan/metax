from metax.core.application.ports.patterns.unit_of_work.unit_of_work import AbstractUnitOfWork
from metax.core.domain.entities.category.entity import Category


class CategoryClassifierService:
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self.__unit_of_work = unit_of_work
        self.__category_map: dict[str, Category] = {}

    async def __load_category_map(self) -> None:
        all_categories = await self.__unit_of_work.category_repo.get_all()
        self.__category_map = {
            word.lower(): category for category in all_categories for word in category.get_helper_words()
        }

    async def classify_category(self, discounted_product_name: str) -> Category | None:
        await self.__load_category_map()
        for word in discounted_product_name.split():
            if word in self.__category_map:
                return self.__category_map[word]
        return None
