from discount_service.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from discount_service.core.application.patterns.event_handler_abc import EventHandler


class DeleteOldDiscountedProducts(EventHandler[NewDiscountedProductsFromRetailerCollected]):
    async def handle_event(self, event: NewDiscountedProductsFromRetailerCollected) -> None:
        # will delete all old data from discounted product repo
        await self._unit_of_work.discounted_product_repo.delete_older_than_and_return_deleted_count(
            date_limit=event.new_products_created_date
        )

        mediator = self.get_mediator()
        await mediator.notify(
            sender=self,
            event=OldDiscountedProductsDeleted(
                new_discounted_products_creation_date=event.new_products_created_date
            ),
        )
