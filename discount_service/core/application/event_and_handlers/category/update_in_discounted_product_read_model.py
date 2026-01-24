from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.domain.entities.category_entity.events import CategoryUpdated


class UpdateCategoryInDiscountedProductReadModel(EventHandler[CategoryUpdated]):
    async def handle(self, event: CategoryUpdated) -> None:
        updated_category = await self.unit_of_work.category_repo.get_by_uuid(event.category_uuid)
        await self.unit_of_work.discounted_product_read_model_repo.update_category(updated_category)
