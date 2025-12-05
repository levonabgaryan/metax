from backend.core.application.patterns.result_type import Error, Result
from backend.core.application.ports.repositories.category import CategoryRepository
from backend.core.application.ports.repositories.errors.errors import EntityWasNotFoundError
from backend.core.domain.entities.category_entity.category import Category


async def process_getting_category_by_name(
    category_repository: CategoryRepository, category_name: str
) -> Result[Category]:
    try:
        category = await category_repository.get_by_name(category_name)
    except EntityWasNotFoundError as exc:
        return Result.from_error(Error.from_main_error(exc=exc))
    else:
        return Result.from_success(category)
