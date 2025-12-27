from backend.core.application.patterns.event_handler_abc import EventHandler
from backend.core.domain.entities.category_entity.events import CategoryNameUpdated


class UpdateCategoryNameInDiscountedProductReadModel(EventHandler[CategoryNameUpdated]):
    async def handle(self, event: CategoryNameUpdated) -> None:
        async with self.unit_of_work as uow:
            await uow.repositories.discounted_product_read_model.update_category_name(
                category_uuid=event.category_uuid,
                new_category_name=event.new_name,
            )
            await uow.commit()
