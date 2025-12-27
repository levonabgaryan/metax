from backend.core.application.patterns.event_handler_abc import EventHandler
from backend.core.domain.entities.category_entity.events import CategoryUpdated


class UpdateCategoryInDiscountedProductReadModel(EventHandler[CategoryUpdated]):
    async def handle(self, event: CategoryUpdated) -> None:
        async with self.unit_of_work as uow:
            updated_category = await self.unit_of_work.repositories.category.get_by_uuid(event.category_uuid)
            await uow.repositories.discounted_product_read_model.update_category(updated_category)
            await uow.commit()
