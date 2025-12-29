from backend.core.application.event_and_handlers.discounted_product.events import OldDiscountedProductsDeleted
from backend.core.application.patterns.event_handler_abc import EventHandler


class SyncDiscountedProductReadModel(EventHandler[OldDiscountedProductsDeleted]):
    async def handle(self, event: OldDiscountedProductsDeleted) -> None:
        # add new data and delete old data from discounted product read model
        async with self.unit_of_work as uow:
            await uow.repositories.discounted_product_read_model.delete_older_than_and_return_deleted_count(
                date_limit=event.new_discounted_products_creation_date
            )
            await uow.repositories.discounted_product_read_model.sync_many_by_date(
                date=event.new_discounted_products_creation_date
            )
            await uow.commit()
