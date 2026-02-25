from discount_service.core.application.commands_and_handlers.category import (
    UpdateCategoryCommandHandler,
)
from discount_service.core.application.commands_and_handlers.retailer import (
    CreateRetailerCommandHandler,
    UpdateRetailerCommandHandler,
    CreateRetailerCommand,
    UpdateRetailerCommand,
)
from discount_service.core.application.event_and_handlers.category.events import CategoryUpdated
from discount_service.core.application.event_and_handlers.category.update_in_discounted_product_read_model import (
    UpdateCategoryInDiscountedProductReadModel,
)
from discount_service.core.application.event_and_handlers.discounted_product.delete_old_discounted_products import (
    DeleteOldDiscountedProducts,
)
from discount_service.core.application.event_and_handlers.discounted_product.events import (
    NewDiscountedProductsFromRetailerCollected,
)
from discount_service.core.application.event_and_handlers.discounted_product.sync_discounted_products_read_model import (
    SyncDiscountedProductReadModel,
)
from discount_service.core.application.event_and_handlers.retailer.update_in_discounted_product_read_model import (
    UpdateRetailerInDiscountedProductReadModel,
)
from discount_service.core.application.patterns.mediator import Mediator, MessageHandler, Message


class Event(Message):
    pass


class Command(Message):
    pass


class MessageBus(Mediator):
    def __init__(
        self,
        update_category_command_handler: UpdateCategoryCommandHandler,
        create_retailer_command_handler: CreateRetailerCommandHandler,
        update_retailer_command_handler: UpdateRetailerCommandHandler,
        delete_old_discounted_products_event_handler: DeleteOldDiscountedProducts,
        sync_discounted_product_read_model: SyncDiscountedProductReadModel,
        update_category_in_discounted_product_read_model: UpdateCategoryInDiscountedProductReadModel,
        update_retailer_in_discounted_product_read_model: UpdateRetailerInDiscountedProductReadModel,
        sync_discounted_products_in_read_model: SyncDiscountedProductReadModel,
    ) -> None:
        self.__update_category_command_handler = update_category_command_handler
        self.__create_retailer_command_handler = create_retailer_command_handler
        self.__update_retailer_command_handler = update_retailer_command_handler
        self.__delete_old_discounted_products_event_handler = delete_old_discounted_products_event_handler
        self.__sync_discounted_product_read_model = sync_discounted_product_read_model
        self.__update_category_in_discounted_product_read_model = update_category_in_discounted_product_read_model
        self.__update_retailer_in_discounted_product_read_model = update_retailer_in_discounted_product_read_model
        self.__sync_discounted_products_in_read_model = sync_discounted_products_in_read_model

    async def notify(self, sender: MessageHandler, message: Message) -> None:
        if isinstance(message, CategoryUpdated) and isinstance(sender, UpdateCategoryCommandHandler):
            await self.__update_category_in_discounted_product_read_model.handle_event(event=message)
        elif isinstance(message, CreateRetailerCommand) and isinstance(sender, CreateRetailerCommandHandler):
            await self.__create_retailer_command_handler.handle_command()
        elif isinstance(message, UpdateRetailerCommand) and isinstance(sender, UpdateRetailerCommandHandler):
            await self.__update_retailer_command_handler.handle()
            await self.__update_retailer_in_discounted_product_read_model.handle()
        elif isinstance(message, NewDiscountedProductsFromRetailerCollected) and isinstance(
            sender, DeleteOldDiscountedProducts
        ):
            await self.__delete_old_discounted_products_event_handler.handle()
            await self.__sync_discounted_products_in_read_model.handle()
