from app.core.application.patterns.result_type import Result
from app.core.application.ports.repositories.category import ICategoryRepository
from app.core.application.use_cases.category.dtos import CreateCategoryRequest, CreateCategoryResponse
from app.core.domain.entities.category_entity.category import Category, CategoryHelperWords


class CreateCategoryUseCase:
    def __init__(
        self,
        category_repository: ICategoryRepository
    ) -> None:
        self.category_repository = category_repository

    async def execute(self, request: CreateCategoryRequest) -> Result[CreateCategoryResponse]:
        helper_words = CategoryHelperWords(request.helper_words)
        category = Category(
            category_uuid=request.category_uuid,
            name=request.name,
            helper_words=helper_words
        )
        await self.category_repository.save(category)
        response = CreateCategoryResponse(
            request.category_uuid,
            request.name,
        )
        return Result(success_value=response)
