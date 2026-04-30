from metax.core.application.ports.backend_patterns.provider.unit_of_work_provider import IUnitOfWorkProvider
from metax.core.domain.entities.category.aggregate_root_entity import Category


class CategoryClassifierService:
    def __init__(self, unit_of_work_provider: IUnitOfWorkProvider) -> None:
        self.__unit_of_work_provider = unit_of_work_provider
        self.__category_map: dict[str, Category] = {}
        self.__category_map_loaded = False

    async def __load_category_map(self) -> None:
        if self.__category_map_loaded:
            return
        uow = await self.__unit_of_work_provider.provide()
        async with uow:
            all_categories = await uow.category_repo.all()
            await uow.commit()

        self.__category_map = {
            helper_word.get_helper_word_text(): category
            for category in all_categories
            for helper_word in category.get_helper_words()
        }

        self.__category_map_loaded = True

    async def classify_category(self, discounted_product_name: str) -> Category | None:
        await self.__load_category_map()
        for word in discounted_product_name.lower().split():
            if word in self.__category_map:
                return self.__category_map[word]
        return None
