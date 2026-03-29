from metax.core.application.ports.patterns.providers.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.domain.entities.category.entity import Category


class CategoryClassifierService:
    def __init__(self, unit_of_work_provider: IUnitOfWorkProvider) -> None:
        self.__unit_of_work_provider = unit_of_work_provider
        self.__category_map: dict[str, Category] = {}
        self.__category_map_loaded = False

    async def __load_category_map(self) -> None:
        if self.__category_map_loaded:
            return
        uow = await self.__unit_of_work_provider.create()
        async with uow:
            all_categories = await uow.category_repo.get_all()
        self.__category_map = {
            word.lower(): category for category in all_categories for word in category.get_helper_words()
        }
        self.__category_map_loaded = True

    async def classify_category(self, discounted_product_name: str) -> Category | None:
        await self.__load_category_map()
        for word in discounted_product_name.split():
            if word in self.__category_map:
                return self.__category_map[word]
        return None
