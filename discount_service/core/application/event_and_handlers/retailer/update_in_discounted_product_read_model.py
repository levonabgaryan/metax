from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.application.event_and_handlers.retailer.events import RetailerUpdated


class UpdateRetailerInDiscountedProductReadModel(EventHandler):
    async def handle_event(self, event: RetailerUpdated) -> None:
        async with self.__unit_of_work as uow:
            updated_retailer = await uow.retailer_repo.get_by_uuid(event.retailer_uuid)
            await uow.discounted_product_read_model_repo.update_retailer(updated_retailer)
            await uow.commit()
