import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, override

from opensearchpy import AsyncOpenSearch

from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax.core.application.read_models.discounted_product import (
    DiscountedProductCategoryReadModel,
    DiscountedProductReadModel,
    DiscountedProductRetailerReadModel,
)
from metax.frameworks_and_drivers.opensearch.indices import discounted_product_read_model


class OpenSearchDiscountedProductReadModelRepository(DiscountedProductReadModelRepository):
    def __init__(self, opensearch_async_client: AsyncOpenSearch) -> None:
        self.__opensearch_async_client = opensearch_async_client
        self.__alias_name = discounted_product_read_model.ALIAS_NAME

    @override
    async def add_many(self, discounted_products: list[DiscountedProductReadModel]) -> None:
        # https://github.com/opensearch-project/opensearch-py/blob/main/samples/bulk/bulk_array.py
        formatted_to_dict: list[dict[str, Any]] = []
        for discounted_product in discounted_products:
            doc_id = discounted_product["uuid_"]

            formatted_to_dict.append({
                "index": {
                    "_index": self.__alias_name,
                    "_id": doc_id,
                }
            })
            formatted_to_dict.append(self._document_body_for_index(discounted_product))
        response = await self.__opensearch_async_client.bulk(body=formatted_to_dict)
        if response.get("errors"):
            msg = "OpenSearch bulk indexing reported errors"
            raise RuntimeError(msg)

    @override
    async def add_one(self, discounted_product: DiscountedProductReadModel) -> None:
        # https://github.com/opensearch-project/opensearch-py/blob/main/guides/async.md#index-documents
        doc_id = discounted_product["uuid_"]
        doc_body = self._document_body_for_index(discounted_product)

        await self.__opensearch_async_client.index(index=self.__alias_name, id=doc_id, body=doc_body)

    @override
    async def delete_older_than_and_return_deleted_count(self, date_limit: datetime) -> int:
        # https://docs.opensearch.org/latest/api-reference/document-apis/delete-by-query/#example-request
        body = {"query": {"range": {"created_at": {"lt": date_limit.isoformat()}}}}
        response = await self.__opensearch_async_client.delete_by_query(
            index=self.__alias_name, body=body, params={"conflicts": "proceed"}
        )
        return int(response.get("deleted", 0))

    @override
    async def all(self) -> AsyncIterator[DiscountedProductReadModel]:
        # Scroll API: size / scroll go in query params (not top-level kwargs on search()).
        # https://github.com/opensearch-project/opensearch-py/blob/main/guides/search.md#basic-pagination
        scroll_keepalive = "2m"
        batch_size = 1000
        response: dict[str, Any] = await self.__opensearch_async_client.search(
            index=self.__alias_name,
            body={"query": {"match_all": {}}},
            params={"scroll": scroll_keepalive, "size": batch_size},
        )
        scroll_id: str | None = response.get("_scroll_id")
        try:
            while True:
                hits = response["hits"]["hits"]
                for hit in hits:
                    yield self._opensearch_source_to_read_model(hit["_id"], hit["_source"])
                    await asyncio.sleep(0)
                if not hits:
                    break
                if not scroll_id:
                    break
                response = await self.__opensearch_async_client.scroll(
                    scroll_id=scroll_id,
                    params={"scroll": scroll_keepalive},
                )
                scroll_id = response.get("_scroll_id")
        finally:
            if scroll_id:
                await self.__opensearch_async_client.clear_scroll(scroll_id=scroll_id)

    @override
    async def get_all_count(self) -> int:
        # https://docs.opensearch.org/latest/api-reference/search-apis/count/#example-requests
        response = await self.__opensearch_async_client.count(
            index=self.__alias_name,
            body={"query": {"match_all": {}}},
        )
        return int(response["count"])

    @override
    async def search_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        query = await self._search_query_body_for_name(name)
        search_body: dict[str, Any] = {
            "query": query,
            "from": offset,
            "size": limit,
            # Relevance first, then stable tie-break so offset pagination does not shuffle
            # documents that share the same score.
            "sort": [
                {"_score": {"order": "desc"}},
                {"_id": {"order": "asc"}},
            ],
        }
        response = await self.__opensearch_async_client.search(
            index=self.__alias_name,
            body=search_body,
        )
        total = self.__total_hits_value(response["hits"]["total"])
        hits = response["hits"]["hits"]
        items = [self._opensearch_source_to_read_model(hit["_id"], hit["_source"]) for hit in hits]
        return items, total

    @override
    async def get_by_uuid(self, uuid_: str) -> DiscountedProductReadModel:
        # https://docs.opensearch.org/latest/api-reference/document-apis/get-documents/#example-request
        response = await self.__opensearch_async_client.get(id=uuid_, index=self.__alias_name)
        document: dict[str, Any] = response["_source"]
        return self._opensearch_source_to_read_model(response["_id"], document)

    @override
    async def update_categories(self, category: DiscountedProductCategoryReadModel) -> None:
        # https://docs.opensearch.org/latest/api-reference/document-apis/update-by-query/#example-requests
        body = {
            "query": {"term": {"category.uuid_": category["uuid_"]}},
            "script": {
                "source": "ctx._source.category = params.cat",
                "lang": "painless",
                "params": {
                    "cat": {
                        "uuid_": category["uuid_"],
                        "name": category["name"],
                        "created_at": category["created_at"],
                        "updated_at": category["updated_at"],
                    }
                },
            },
        }
        await self.__opensearch_async_client.update_by_query(
            index=self.__alias_name,
            body=body,
        )

    @override
    async def update_retailers(self, retailer: DiscountedProductRetailerReadModel) -> None:
        # https://docs.opensearch.org/latest/api-reference/document-apis/update-by-query/#example-requests
        body = {
            "query": {"term": {"retailer.uuid_": retailer["uuid_"]}},
            "script": {
                "source": "ctx._source.retailer = params.ret",
                "lang": "painless",
                "params": {
                    "ret": {
                        "uuid_": retailer["uuid_"],
                        "name": retailer["name"],
                        "created_at": retailer["created_at"],
                        "updated_at": retailer["updated_at"],
                        "home_page_url": retailer["home_page_url"],
                        "phone_number": retailer["phone_number"],
                    }
                },
            },
        }

        await self.__opensearch_async_client.update_by_query(
            index=self.__alias_name,
            body=body,
        )

    def _document_body_for_index(self, read_model: DiscountedProductReadModel) -> dict[str, Any]:
        """Serialize read model to the OpenSearch document (same nested shape as mappings).

        Returns:
            Body for ``index`` / ``bulk`` (no ``uuid_``; stored as ``_id``).
        """
        retailer = read_model["retailer"]
        body: dict[str, Any] = {
            "name": read_model["name"],
            "real_price": read_model["real_price"],
            "discounted_price": read_model["discounted_price"],
            "created_at": read_model["created_at"],
            "updated_at": read_model["updated_at"],
            "url": read_model["url"],
            "retailer": {
                "uuid_": retailer["uuid_"],
                "name": retailer["name"],
                "created_at": retailer["created_at"],
                "updated_at": retailer["updated_at"],
                "home_page_url": retailer["home_page_url"],
                "phone_number": retailer["phone_number"],
            },
        }
        if "category" in read_model:
            category = read_model["category"]
            body["category"] = {
                "uuid_": category["uuid_"],
                "name": category["name"],
                "created_at": category["created_at"],
                "updated_at": category["updated_at"],
            }
        return body

    @staticmethod
    def _opensearch_source_to_read_model(uuid_: str, source: dict[str, Any]) -> DiscountedProductReadModel:
        """Map OpenSearch ``_source`` to ``DiscountedProductReadModel`` (same keys as TypedDict).

        Returns:
            Value satisfying ``DiscountedProductReadModel``.
        """
        created_at = source["created_at"]
        updated_at = source["updated_at"]
        src_retailer = source["retailer"]
        r_created = src_retailer["created_at"]
        r_updated = src_retailer["updated_at"]
        item: DiscountedProductReadModel = {
            "uuid_": uuid_,
            "name": source["name"],
            "real_price": source["real_price"],
            "discounted_price": source["discounted_price"],
            "created_at": created_at,
            "updated_at": updated_at,
            "url": source["url"],
            "retailer": {
                "uuid_": src_retailer["uuid_"],
                "name": src_retailer["name"],
                "created_at": r_created,
                "updated_at": r_updated,
                "home_page_url": src_retailer["home_page_url"],
                "phone_number": src_retailer["phone_number"],
            },
        }
        if "category" in source:
            category_src = source["category"]
            c_created = category_src["created_at"]
            c_updated = category_src["updated_at"]
            item["category"] = DiscountedProductCategoryReadModel(
                uuid_=category_src["uuid_"],
                created_at=c_created,
                updated_at=c_updated,
                name=category_src["name"],
            )
        return item

    async def _search_query_body_for_name(self, name: str) -> dict[str, Any]:
        translit_res = await self.__opensearch_async_client.indices.analyze(
            body={
                "tokenizer": "keyword",
                "filter": [{"type": "icu_transform", "id": "Latin-Armenian"}],
                "text": name,
            }
        )
        armenian_query = translit_res["tokens"][0]["token"]
        return {
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

    @staticmethod
    def __total_hits_value(total: Any) -> int:
        if isinstance(total, dict):
            return int(total["value"])
        return int(total)
