import asyncio
from typing import Any

from opensearchpy import AsyncOpenSearch, NotFoundError

from .indices.discounted_product_read_model import DISCOUNTED_PRODUCT_READ_MODEL_METADATA

INDICES_METADATA = [DISCOUNTED_PRODUCT_READ_MODEL_METADATA]


async def opensearch_migrate_index(
    client: AsyncOpenSearch,
    new_index_name: str,
    alias_name: str,
    index_body: dict[str, Any],
) -> None:
    if not await client.indices.exists(index=new_index_name):
        old_index_name = None
        try:
            response: dict[str, Any] = await client.indices.get_alias(name=alias_name)
            old_index_name = list(response.keys())[0]
        except NotFoundError:
            pass

        await client.indices.create(index=new_index_name, body=index_body)

        index_changed = old_index_name is not None
        if index_changed and old_index_name != new_index_name:
            await client.reindex(
                body={
                    "source": {"index": old_index_name},
                    "dest": {"index": new_index_name},
                },
                wait_for_completion=True,
            )

            await client.indices.update_aliases(
                body={
                    "actions": [
                        {"remove": {"index": old_index_name, "alias": alias_name}},
                        {"add": {"index": new_index_name, "alias": alias_name}},
                    ]
                }
            )
            await client.indices.delete(index=old_index_name)
    else:
        await client.indices.put_mapping(
            index=new_index_name,
            body=index_body["mappings"],
        )
    if not await client.indices.exists_alias(name=alias_name):
        await client.indices.put_alias(index=new_index_name, name=alias_name)


async def migrate_indices(client: AsyncOpenSearch) -> None:
    tasks = [
        opensearch_migrate_index(
            client=client,
            new_index_name=metadata["index_name"],
            alias_name=metadata["alias_name"],
            index_body=metadata["index_body"],
        )
        for metadata in INDICES_METADATA
    ]
    if tasks:
        await asyncio.gather(*tasks)


async def delete_all_indices(client: AsyncOpenSearch) -> None:
    tasks = [client.indices.delete(index=metadata["index_name"]) for metadata in INDICES_METADATA]
    if tasks:
        await asyncio.gather(*tasks)
