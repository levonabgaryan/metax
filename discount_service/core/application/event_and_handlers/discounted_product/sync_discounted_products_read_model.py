from discount_service.core.application.event_and_handlers.discounted_product.events import (
    OldDiscountedProductsDeleted,
)
from discount_service.core.application.patterns.event_handler_abc import EventHandler
from discount_service.core.application.ports.repositories.entites_repositories.discounted_product import (
    DiscountedProductRepository,
    DiscountedProductWithDetails,
)
from discount_service.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)
from discount_service.core.application.read_models.discounted_product import DiscountedProductReadModel


class SyncDiscountedProductReadModel(EventHandler[OldDiscountedProductsDeleted]):
    async def handle(self, event: OldDiscountedProductsDeleted) -> None:
        # add new data and delete old data from discounted product read model

        batch_size = 500
        current_batch = []
        date_limit = event.new_discounted_products_creation_date

        repo: DiscountedProductRepository = self.__unit_of_work.discounted_product_repo
        read_model_repo: IDiscountedProductReadModelRepository = (
            self.__unit_of_work.discounted_product_read_model_repo
        )

        discounted_product: DiscountedProductWithDetails
        async for discounted_product in repo.get_all_by_date(date_=date_limit):
            current_batch.append(discounted_product)

            if len(current_batch) >= batch_size:
                await read_model_repo.add_many([to_read_model(p) for p in current_batch])
                current_batch.clear()

        if current_batch:
            await read_model_repo.add_many([to_read_model(p) for p in current_batch])

        await read_model_repo.delete_older_than_and_return_deleted_count(date_limit=date_limit)


def to_read_model(discounted_product_with_details: DiscountedProductWithDetails) -> DiscountedProductReadModel:
    return DiscountedProductReadModel(
        discounted_product_uuid=str(discounted_product_with_details.entity.get_uuid()),
        name=discounted_product_with_details.entity.get_name(),
        real_price=float(discounted_product_with_details.entity.get_real_price()),
        discounted_price=float(discounted_product_with_details.entity.get_discounted_price()),
        category_uuid=str(discounted_product_with_details.entity.get_category_uuid())
        if discounted_product_with_details.entity.has_category()
        else None,
        category_name=str(discounted_product_with_details.category_name)
        if discounted_product_with_details.entity.has_category()
        else None,
        retailer_uuid=str(discounted_product_with_details.entity.get_retailer_uuid()),
        retailer_name=str(discounted_product_with_details.retailer_name),
        url=str(discounted_product_with_details.entity.get_url()),
        created_at=discounted_product_with_details.entity.get_created_at().isoformat(),
    )
