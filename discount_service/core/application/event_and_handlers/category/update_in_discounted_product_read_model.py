from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.application.event_and_handlers.category.events import CategoryUpdated


class UpdateCategoryInDiscountedProductReadModel(EventHandler):
    async def handle_event(self, event: CategoryUpdated) -> None:
        updated_category = await self.__unit_of_work.category_repo.get_by_uuid(event.category_uuid)
        await self.__unit_of_work.discounted_product_read_model_repo.update_category(updated_category)
