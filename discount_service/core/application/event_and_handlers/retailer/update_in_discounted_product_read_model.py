from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.domain.entities.retailer_entity.events import RetailerUpdated


class UpdateRetailerInDiscountedProductReadModel(EventHandler[RetailerUpdated]):
    async def handle(self, event: RetailerUpdated) -> None:
        async with self.unit_of_work as uow:
            updated_retailer = await uow.repositories.retailer.get_by_uuid(event.retailer_uuid)
            await uow.repositories.discounted_product_read_model.update_retailer(updated_retailer)
            await uow.commit()
