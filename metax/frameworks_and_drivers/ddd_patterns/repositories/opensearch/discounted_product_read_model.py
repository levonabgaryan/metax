import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, override

from opensearchpy import AsyncOpenSearch

from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    IDiscountedProductReadModelRepository,
)
from metax.core.application.read_models.discounted_product import DiscountedProductReadModel
from metax.frameworks_and_drivers.opensearch.indices import discounted_product_read_model


def _opensearch_source_to_read_model(uuid_: str, source: dict[str, Any]) -> DiscountedProductReadModel:
    item: DiscountedProductReadModel = {
        "uuid_": uuid_,
        "name": source["name"],
        "real_price": source["real_price"],
        "discounted_price": source["discounted_price"],
        "retailer_uuid": source["retailer_uuid"],
        "retailer_name": source["retailer_name"],
        "url": source["url"],
        "created_at": source["created_at"],
    }
    category_uuid: str | None = source.get("category_uuid")
    if category_uuid is not None:
        item["category_uuid"] = category_uuid
    category_name: str | None = source.get("category_name")
    if category_name is not None:
        item["category_name"] = category_name
    return item


class OpenSearchDiscountedProductReadModelRepository(IDiscountedProductReadModelRepository):
    def __init__(self, opensearch_async_client: AsyncOpenSearch) -> None:
        self.__opensearch_async_client = opensearch_async_client
        self.__alias_name = discounted_product_read_model.ALIAS_NAME

    @override
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        # https://docs.opensearch.org/latest/api-reference/document-apis/delete-by-query/#example-request
        body = {"query": {"range": {"created_at": {"lt": date_limit.isoformat()}}}}
        response = await self.__opensearch_async_client.delete_by_query(
            index=self.__alias_name, body=body, params={"conflicts": "proceed"}
        )

        return int(response.get("deleted", 0))

    @override
    async def update_category_names_by_category_uuid(self, category_uuid: str, new_category_name: str) -> None:
        # https://docs.opensearch.org/latest/api-reference/document-apis/update-by-query/#example-requests
        body = {
            "query": {"term": {"category_uuid": category_uuid}},
            "script": {
                "source": "ctx._source.category_name = params.new_name",
                "lang": "painless",
                "params": {"new_name": new_category_name},
            },
        }
        await self.__opensearch_async_client.update_by_query(
            index=self.__alias_name,
            body=body,
        )

    @override
    async def update_retailer_names_by_retailer_uuid(self, retailer_uuid: str, new_retailer_name: str) -> None:
        # https://docs.opensearch.org/latest/api-reference/document-apis/update-by-query/#example-requests
        body = {
            "query": {"term": {"retailer_uuid": retailer_uuid}},
            "script": {
                "source": "ctx._source.retailer_name = params.new_name",
                "lang": "painless",
                "params": {"new_name": new_retailer_name},
            },
        }

        await self.__opensearch_async_client.update_by_query(
            index=self.__alias_name,
            body=body,
        )

    @override
    async def get_all(self) -> AsyncIterator[DiscountedProductReadModel]:
        # https://github.com/opensearch-project/opensearch-py/blob/main/guides/search.md#basic-pagination
        response: dict[str, Any] = await self.__opensearch_async_client.search(
            index=self.__alias_name,
            size=5,
        )
        hits = response["hits"]["hits"]
        for hit in hits:
            yield _opensearch_source_to_read_model(hit["_id"], hit["_source"])
            await asyncio.sleep(0)

    @override
    async def get_all_count(self) -> int:
        # https://docs.opensearch.org/latest/api-reference/search-apis/count/#example-requests
        response = await self.__opensearch_async_client.count(
            index=self.__alias_name,
            body={"query": {"match_all": {}}},
        )
        return int(response["count"])

    @override
    async def add_one(self, discounted_product: DiscountedProductReadModel) -> None:
        # https://github.com/opensearch-project/opensearch-py/blob/main/guides/async.md#index-documents
        doc_id = discounted_product["uuid_"]
        doc_body = {k: v for k, v in discounted_product.items() if k != "uuid_"}

        await self.__opensearch_async_client.index(index=self.__alias_name, id=doc_id, body=doc_body)

    @override
    async def add_many(self, discounted_products: list[DiscountedProductReadModel]) -> None:
        # https://github.com/opensearch-project/opensearch-py/blob/main/samples/bulk/bulk_array.py
        formatted_to_dict: list[dict[str, Any] | DiscountedProductReadModel] = []
        for discounted_product in discounted_products:
            doc_id = discounted_product["uuid_"]

            formatted_to_dict.append({
                "index": {
                    "_index": self.__alias_name,
                    "_id": doc_id,
                }
            })
            doc_body = {k: v for k, v in discounted_product.items() if k != "uuid_"}
            formatted_to_dict.append(doc_body)
        response = await self.__opensearch_async_client.bulk(body=formatted_to_dict)
        if response.get("errors"):
            msg = "OpenSearch bulk indexing reported errors"
            raise RuntimeError(msg)

    @override
    async def get_by_uuid(self, uuid_: str) -> DiscountedProductReadModel:
        # https://docs.opensearch.org/latest/api-reference/document-apis/get-documents/#example-request
        response = await self.__opensearch_async_client.get(id=uuid_, index=self.__alias_name)
        document: dict[str, Any] = response["_source"]
        return _opensearch_source_to_read_model(response["_id"], document)

    @override
    async def get_by_name(
        self,
        name: str,
        cursor_: str | None = None,  # page id
        chunk_size: int = 100,
    ) -> tuple[list[DiscountedProductReadModel], str | None]:
        # First request
        scroll_id = cursor_
        if scroll_id is None:
            translit_res = await self.__opensearch_async_client.indices.analyze(
                body={
                    "tokenizer": "keyword",
                    "filter": [{"type": "icu_transform", "id": "Latin-Armenian"}],
                    "text": name,
                }
            )

            armenian_query = translit_res["tokens"][0]["token"]

            search_body = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": name,
                                    "fields": ["name.eng", "name.rus", "name.arm"],
                                    "type": "most_fields",
                                }
                            },
                            {"match": {"name.arm": {"query": armenian_query, "boost": 1.5}}},
                        ]
                    }
                }
            }

            response = await self.__opensearch_async_client.search(
                index=self.__alias_name,
                body=search_body,
                scroll="5m",
                size=chunk_size,
            )

        # Next pages
        else:
            response = await self.__opensearch_async_client.scroll(
                scroll_id=scroll_id,
                scroll="5m",
            )

        new_scroll_id = response.get("_scroll_id")
        hits = response["hits"]["hits"]

        items = [_opensearch_source_to_read_model(hit["_id"], hit["_source"]) for hit in hits]

        # No more data → cleanup
        if not hits and new_scroll_id:
            await self.__opensearch_async_client.clear_scroll(scroll_id=new_scroll_id)
            return [], None

        return items, new_scroll_id
