import asyncio
from datetime import datetime
from typing import AsyncIterator, Any

from opensearchpy import AsyncOpenSearch

from discount_service.core.application.ports.repositories.read_models_repositories.discounted_product_read_model import (
    IDiscountedProductReadModelRepository,
)
from discount_service.core.application.read_models.discounted_product import DiscountedProductReadModel
from discount_service.core.domain.entities.category_entity.category import Category

from discount_service.core.domain.entities.retailer_entity.retailer import Retailer

from discount_service.frameworks_and_drivers.opensearch.indices import discounted_product_read_model


class OpenSearchDiscountedProductReadModelRepository(IDiscountedProductReadModelRepository):
    def __init__(self, opensearch_async_client: AsyncOpenSearch) -> None:
        self.__opensearch_async_client = opensearch_async_client

    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        # https://docs.opensearch.org/latest/api-reference/document-apis/delete-by-query/#example-request
        body = {"query": {"range": {"created_at": {"lt": date_limit.isoformat()}}}}
        response = await self.__opensearch_async_client.delete_by_query(
            index=discounted_product_read_model.ALIAS_NAME,
            body=body,
            conflicts="proceed",
        )

        return int(response.get("deleted", 0))

    async def update_category(self, updated_category: Category) -> None:
        # https://docs.opensearch.org/latest/api-reference/document-apis/update-by-query/#example-requests
        body = {
            "query": {"term": {"category_uuid": str(updated_category.get_uuid())}},
            "script": {
                "source": "ctx._source.category_name = params.new_name",
                "lang": "painless",
                "params": {"new_name": updated_category.get_name()},
            },
        }
        await self.__opensearch_async_client.update_by_query(
            index=discounted_product_read_model.ALIAS_NAME,
            body=body,
        )

    async def update_retailer(self, updated_retailer: Retailer) -> None:
        # https://docs.opensearch.org/latest/api-reference/document-apis/update-by-query/#example-requests
        body = {
            "query": {"term": {"retailer_uuid": str(updated_retailer.get_uuid())}},
            "script": {
                "source": "ctx._source.retailer_name = params.new_name",
                "lang": "painless",
                "params": {"new_name": updated_retailer.get_name()},
            },
        }

        await self.__opensearch_async_client.update_by_query(
            index=discounted_product_read_model.ALIAS_NAME,
            body=body,
        )

    async def get_all(self) -> AsyncIterator[DiscountedProductReadModel]:
        # https://github.com/opensearch-project/opensearch-py/blob/main/guides/search.md#basic-pagination
        response: dict[str, Any] = await self.__opensearch_async_client.search(
            index=discounted_product_read_model.ALIAS_NAME,
            size=5,
        )
        hits = response["hits"]["hits"]
        for hit in hits:
            source = hit["_source"]
            source["discounted_product_uuid"] = hit["_id"]
            yield DiscountedProductReadModel(
                discounted_product_uuid=source["discounted_product_uuid"],
                name=source["name"],
                real_price=source["real_price"],
                discounted_price=source["discounted_price"],
                category_uuid=source["category_uuid"],
                category_name=source["category_name"],
                retailer_uuid=source["retailer_uuid"],
                retailer_name=source["retailer_name"],
                created_at=source["created_at"],
            )
            await asyncio.sleep(0)

    async def get_all_count(self) -> int:
        # https://docs.opensearch.org/latest/api-reference/search-apis/count/#example-requests
        response = await self.__opensearch_async_client.count(
            index=discounted_product_read_model.ALIAS_NAME,
            body={"query": {"match_all": {}}},
        )
        return int(response["count"])

    async def add_one(self, discounted_product: DiscountedProductReadModel) -> None:
        # https://github.com/opensearch-project/opensearch-py/blob/main/guides/async.md#index-documents
        id_ = discounted_product.pop("discounted_product_uuid")
        await self.__opensearch_async_client.index(
            index=discounted_product_read_model.ALIAS_NAME, id=id_, body=discounted_product
        )

    async def add_many(self, discounted_products: list[DiscountedProductReadModel]) -> None:
        # https://github.com/opensearch-project/opensearch-py/blob/main/samples/bulk/bulk_array.py
        formatted_to_dict: list[dict[str, Any] | DiscountedProductReadModel] = []
        for discounted_product in discounted_products:
            doc_id = discounted_product["discounted_product_uuid"]

            formatted_to_dict.append(
                {
                    "index": {
                        "_index": discounted_product_read_model.ALIAS_NAME,
                        "_id": doc_id,
                    }
                }
            )
            doc_body = {k: v for k, v in discounted_product.items() if k != "discounted_product_uuid"}
            formatted_to_dict.append(doc_body)
        response = await self.__opensearch_async_client.bulk(body=formatted_to_dict)
        if response.get("errors"):
            raise

    async def get_by_uuid(self, discounted_product_read_model_uuid: str) -> DiscountedProductReadModel:
        # https://docs.opensearch.org/latest/api-reference/document-apis/get-documents/#example-request
        response = await self.__opensearch_async_client.get(
            id=discounted_product_read_model_uuid, index=discounted_product_read_model.ALIAS_NAME
        )
        document: dict[str, Any] = response["_source"]

        return DiscountedProductReadModel(
            discounted_product_uuid=response["_id"],
            name=document["name"],
            real_price=document["real_price"],
            discounted_price=document["discounted_price"],
            category_uuid=document.get("category_uuid"),
            category_name=document.get("category_name"),
            retailer_uuid=document["retailer_uuid"],
            retailer_name=document["retailer_name"],
            url=document.get("url"),
            created_at=document["created_at"],
        )
