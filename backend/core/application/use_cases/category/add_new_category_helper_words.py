from backend.core.application.patterns.empty_dto import EmptyResponse
from backend.core.application.patterns.result_type import EmptyValue, Error, Result
from backend.core.application.ports.repositories.category import ICategoryRepository
from backend.core.application.use_cases.category.dtos import AddNewCategoryHelperWordsRequest
from backend.core.application.use_cases.category.utils import process_getting_category_by_name
from backend.core.domain.entities.category_entity.category import Category
from backend.core.domain.entities.category_entity.errors.errors import DuplicateCategoryHelperWordsError


class AddNewCategoryHelperWordsUseCase:
    def __init__(self, category_repository: ICategoryRepository) -> None:
        self.category_repository = category_repository

    async def execute(self, request: AddNewCategoryHelperWordsRequest) -> Result[EmptyResponse]:
        category_result = await process_getting_category_by_name(
            category_repository=self.category_repository, category_name=request.category_name
        )
        if category_result.is_failure:
            return Result.from_error(category_result.get_error_value())
        category = category_result.get_success_value()

        updated_result = await self.__process_adding_helper_words_and_save(
            category=category, new_words=request.new_helper_words
        )
        if updated_result.is_failure:
            return Result.from_error(updated_result.get_error_value())

        return Result.from_success(EmptyResponse())

    async def __process_adding_helper_words_and_save(
        self, category: Category, new_words: frozenset[str]
    ) -> Result[EmptyValue]:
        try:
            category.add_new_helper_words(new_words=new_words)
        except DuplicateCategoryHelperWordsError as exc:
            return Result.from_error(value=Error.from_main_error(exc=exc))
        else:
            await self.category_repository.save(category)
            return Result.from_success(EmptyValue())
