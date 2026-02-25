from discount_service.core.application.commands_handlers.category import (
    UpdateCategoryCommandHandler,
)
from discount_service.core.application.commands_handlers.retailer import (
    UpdateRetailerCommandHandler,
)
from discount_service.core.application.event_handlers.category.events import CategoryUpdated
from discount_service.core.application.event_handlers.category.update_in_discounted_product_read_model import (
    UpdateCategoryInDiscountedProductReadModel,
)
from discount_service.core.application.event_handlers.discounted_product.delete_old_discounted_products import (
    DeleteOldDiscountedProducts,
)
from discount_service.core.application.event_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
    OldDiscountedProductsDeleted,
)
from discount_service.core.application.event_handlers.discounted_product.sync_discounted_products_read_model import (
    SyncDiscountedProductReadModel,
)
from discount_service.core.application.event_handlers.retailer.events import RetailerUpdated
from discount_service.core.application.event_handlers.retailer.update_in_discounted_product_read_model import (
    UpdateRetailerInDiscountedProductReadModel,
)
from discount_service.core.application.patterns.mediator import Mediator, BaseHandler
from discount_service.core.application.patterns.event import Event
from discount_service.core.application.use_cases.discounted_product.collect_discounted_products import (
    CollectDiscountedProducts,
)


class EventBus(Mediator):
    def __init__(
        self,
        delete_old_discounted_products_event_handler: DeleteOldDiscountedProducts,
        update_category_in_discounted_product_read_model_event_handler: UpdateCategoryInDiscountedProductReadModel,
        update_retailer_in_discounted_product_read_model_event_handler: UpdateRetailerInDiscountedProductReadModel,
        sync_discounted_products_in_read_model_event_handler: SyncDiscountedProductReadModel,
    ) -> None:
        self.__delete_old_discounted_products_event_handler = delete_old_discounted_products_event_handler
        self.__update_category_in_discounted_product_read_model_event_handler = (
            update_category_in_discounted_product_read_model_event_handler
        )
        self.__update_retailer_in_discounted_product_read_model_event_handler = (
            update_retailer_in_discounted_product_read_model_event_handler
        )
        self.__sync_discounted_products_in_read_model_event_handler = (
            sync_discounted_products_in_read_model_event_handler
        )
        self.set_mediators_on_event_handlers()

    def set_mediators_on_event_handlers(self) -> None:
        self.__delete_old_discounted_products_event_handler.set_mediator(mediator=self)
        self.__update_category_in_discounted_product_read_model_event_handler.set_mediator(mediator=self)
        self.__update_retailer_in_discounted_product_read_model_event_handler.set_mediator(mediator=self)
        self.__sync_discounted_products_in_read_model_event_handler.set_mediator(mediator=self)

    async def notify(self, sender: BaseHandler, event: Event) -> None:
        if isinstance(event, CategoryUpdated) and isinstance(sender, UpdateCategoryCommandHandler):
            await self.__update_category_in_discounted_product_read_model_event_handler.handle_event(event=event)
        elif isinstance(event, RetailerUpdated) and isinstance(sender, UpdateRetailerCommandHandler):
            await self.__update_retailer_in_discounted_product_read_model_event_handler.handle_event(event=event)
        elif isinstance(event, NewDiscountedProductsFromRetailerCollected) and isinstance(
            sender, CollectDiscountedProducts
        ):
            await self.__delete_old_discounted_products_event_handler.handle_event(event=event)
        elif isinstance(event, OldDiscountedProductsDeleted) and isinstance(
            sender, SyncDiscountedProductReadModel
        ):
            await self.__sync_discounted_products_in_read_model_event_handler.handle_event(event=event)
