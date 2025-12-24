from backend.core.application.patterns.use_case_abc import UseCase, EmptyResponseDTO
from backend.core.application.use_cases.category.dtos import DeleteHelperWordsRequest


class DeleteHelperWordsUseCase(UseCase[DeleteHelperWordsRequest, EmptyResponseDTO]):
    async def execute(self, request: DeleteHelperWordsRequest) -> EmptyResponseDTO:
        async with self.unit_of_work as uow:
            repo = uow.repositories.category
            category = await repo.get_by_uuid(request.category_uuid)
            category.delete_helper_words(request.words_to_delete)
            await repo.update_helper_words(updated_category=category)
            await uow.commit()
        return EmptyResponseDTO()
