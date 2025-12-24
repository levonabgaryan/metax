from backend.core.application.patterns.use_case_abc import UseCase, EmptyResponseDTO
from backend.core.application.use_cases.category.dtos import AddHelperWordsRequest


class AddHelperWordsUseCase(UseCase[AddHelperWordsRequest, EmptyResponseDTO]):
    async def execute(self, request: AddHelperWordsRequest) -> EmptyResponseDTO:
        async with self.unit_of_work as uow:
            repo = uow.repositories.category
            category = await repo.get_by_uuid(request.category_uuid)
            category.add_new_helper_words(request.new_helper_words)
            await repo.update_helper_words(updated_category=category)
            await uow.commit()
        return EmptyResponseDTO()
