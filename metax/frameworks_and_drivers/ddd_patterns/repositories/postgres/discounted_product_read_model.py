"""Postgres + pgvector implementation of the discounted-product search read model.

Search runs directly against the ``discounted_products`` table (no separate read store):
retailer/category fields are read live via joins, and ranking is semantic — ordered by cosine
distance between the query embedding and each product's ``name_embedding`` — with a whole-word
lexical boost (``~*`` at word boundaries) so a literal brand/SKU query floats its exact matches
to the top instead of being buried under close semantic neighbours. The lexical boost runs against
both the original name and its Latin transliteration (``name_translit``), so a cross-script phonetic
query ("karag") still matches the Armenian name ("կարագ").
"""

from __future__ import annotations

import re
from typing import Any, override

from asgiref.sync import sync_to_async
from django.db import connection
from django.db.backends.utils import CursorWrapper

from metax.core.application.ports.ddd_patterns.repository.read_models_repositories.discounted_product_read_model import (  # noqa: E501
    DiscountedProductReadModelRepository,
)
from metax.core.application.ports.ddd_patterns.service.embedding_service import EmbeddingService
from metax.core.application.read_models.discounted_product import (
    DiscountedProductCategoryReadModel,
    DiscountedProductReadModel,
)
from metax.frameworks_and_drivers.ddd_patterns.repositories.postgres.transliteration import (
    transliterate_armenian_to_latin,
)

# Relevance gate for *non-lexical* (pure-semantic) matches: a product with no whole-word lexical
# hit is only admitted when its cosine distance (0 = identical, 2 = opposite) is within this
# ceiling. Whole-word lexical matches are always included regardless of distance and rank first
# (see ``exact_match`` in ``_SEARCH_ORDER_BY``), so search is lexical-primary with a semantic
# fallback. The ceiling is deliberately tight: on this data relevant/irrelevant items overlap in
# the ~0.42-0.50 band, so a looser gate floods results with unrelated neighbours (a bare ``ձու``
# query pulled in fish/giraffe/watermelon). Tightening it makes weak queries return few/none
# instead of a page of noise, without dropping lexical matches. Tune empirically against real
# queries; lower it for stricter results, raise it for more semantic recall.
_MAX_COSINE_DISTANCE = 0.42


def _word_match_pattern(name: str) -> str:
    r"""POSIX regex (for ``~*``) matching the query only at whole-word boundaries.

    Substring matching (``ILIKE '%name%'``) is linguistically wrong here: a short query like
    ``ձու`` (egg) is a literal substring of unrelated words such as ``ձուկ`` (fish) or
    ``Ընձուղտ`` (giraffe). ``\y`` anchors both ends to word boundaries so those no longer match
    lexically; semantically-close items still surface via the cosine-distance branch.

    ``re.escape`` neutralises regex metacharacters in the user query (it never escapes
    alphanumerics, so it produces no illegal ``\<letter>`` escapes under Postgres ARE).

    Returns:
        A pattern usable as a parameter to the ``~*`` operator.
    """
    return r"\y" + re.escape(name) + r"\y"


# Columns selected for every search/get query, in the order ``_row_to_read_model`` expects.
_READ_MODEL_COLUMNS = """
    dp.uuid, dp.created_at, dp.updated_at, dp.name, dp.real_price, dp.discounted_price,
    dp.url, dp.image_url,
    r.uuid, r.created_at, r.updated_at, r.name, r.home_page_url, r.phone_number,
    c.uuid, c.created_at, c.updated_at, c.name
"""

_READ_MODEL_JOINS = """
    FROM discounted_products dp
    INNER JOIN retailers r ON dp.retailer_uuid = r.uuid
    LEFT JOIN categories c ON dp.category_uuid = c.uuid
"""

# Whole-word lexical matches first, then closest semantic neighbour, then deepest discount,
# then a stable tie-break for consistent offset pagination.
_SEARCH_ORDER_BY = """
    ORDER BY exact_match DESC,
             distance ASC,
             CASE WHEN dp.real_price > 0
                  THEN (dp.real_price - dp.discounted_price) / dp.real_price
                  ELSE 0 END DESC,
             dp.uuid ASC
"""


def _confidence_from_distance(distance: float | None) -> float:
    """Convert a cosine distance (0 = identical, higher = farther) to a 0..1 confidence score.

    Returns:
        ``1.0`` for an identical match down to ``0.0``, clamped; ``0.0`` when distance is unknown.
    """
    if distance is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 - float(distance)))


def _vector_literal(vector: list[float]) -> str:
    """Render an embedding as the pgvector text form ``[a,b,c]`` for a ``::vector`` cast.

    Returns:
        The bracketed, comma-separated literal accepted by a ``%s::vector`` parameter.
    """
    return "[" + ",".join(repr(value) for value in vector) + "]"


def _row_to_read_model(row: tuple[Any, ...]) -> DiscountedProductReadModel:
    """Map a joined result row (column order = ``_READ_MODEL_COLUMNS``) to the read model.

    Returns:
        The ``DiscountedProductReadModel`` projection for the row.
    """
    item: DiscountedProductReadModel = {
        "uuid_": str(row[0]),
        "created_at": row[1].isoformat(),
        "updated_at": row[2].isoformat(),
        "name": row[3],
        "real_price": float(row[4]),
        "discounted_price": float(row[5]),
        "url": row[6],
        "retailer": {
            "uuid_": str(row[8]),
            "created_at": row[9].isoformat(),
            "updated_at": row[10].isoformat(),
            "name": row[11],
            "home_page_url": row[12],
            "phone_number": row[13],
        },
    }
    if row[7] is not None:
        item["image_url"] = row[7]
    # category columns are NULL when the product is uncategorised (LEFT JOIN).
    if row[14] is not None:
        item["category"] = DiscountedProductCategoryReadModel(
            uuid_=str(row[14]),
            created_at=row[15].isoformat(),
            updated_at=row[16].isoformat(),
            name=row[17],
        )
    return item


class PostgresDiscountedProductReadModelRepository(DiscountedProductReadModelRepository):
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.__embedding_service = embedding_service

    @override
    async def embed_pending(self, batch_size: int = 500) -> int:
        total = 0
        while True:
            batch = await sync_to_async(self.__fetch_unembedded)(batch_size)
            if not batch:
                break
            uuids = [uuid_ for uuid_, _ in batch]
            names = [name for _, name in batch]
            vectors = await self.__embedding_service.embed_documents(names)
            await sync_to_async(self.__store_embeddings)(uuids, vectors)
            total += len(batch)
            if len(batch) < batch_size:
                break
        return total

    @override
    async def count_pending(self) -> int:
        return await sync_to_async(self.__count_unembedded)()

    @override
    async def search_by_name(
        self,
        name: str,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        query_vector = await self.__embedding_service.embed_query(name)
        return await sync_to_async(self.__search_sync)(name, query_vector, offset, limit, None, None)

    @override
    async def search_by_name_and_by_retailer_uuid(
        self,
        name: str,
        retailer_uuid: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        query_vector = await self.__embedding_service.embed_query(name)
        return await sync_to_async(self.__search_sync)(name, query_vector, offset, limit, retailer_uuid, None)

    @override
    async def search_by_name_and_by_category_uuid(
        self,
        name: str,
        category_uuid: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        query_vector = await self.__embedding_service.embed_query(name)
        return await sync_to_async(self.__search_sync)(name, query_vector, offset, limit, None, category_uuid)

    @override
    async def search_by_category_uuid(
        self,
        category_uuid: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        return await sync_to_async(self.__search_by_category_sync)(category_uuid, offset, limit)

    @override
    async def get_by_uuid(self, uuid_: str) -> DiscountedProductReadModel:
        return await sync_to_async(self.__get_by_uuid_sync)(uuid_)

    def __search_sync(
        self,
        name: str,
        query_vector: list[float],
        offset: int,
        limit: int,
        retailer_uuid: str | None,
        category_uuid: str | None,
    ) -> tuple[list[DiscountedProductReadModel], int]:
        vector = _vector_literal(query_vector)
        word_pattern = _word_match_pattern(name)
        # Cross-script phonetic match: a Latin query ("karag") matches the transliterated Armenian
        # name ("կարագ" -> "karag"), and an Armenian query transliterates to the same key.
        translit_pattern = _word_match_pattern(transliterate_armenian_to_latin(name))
        # Param order must match the %s placeholders top-to-bottom: SELECT exact_match
        # (word_pattern, translit_pattern), SELECT distance (vector), WHERE (word_pattern,
        # translit_pattern, vector), optional filters, then LIMIT/OFFSET.
        params: list[Any] = [word_pattern, translit_pattern, vector, word_pattern, translit_pattern, vector]
        filters = ""
        if retailer_uuid is not None:
            filters += " AND dp.retailer_uuid = %s"
            params.append(retailer_uuid)
        if category_uuid is not None:
            filters += " AND dp.category_uuid = %s"
            params.append(category_uuid)
        params.extend([limit, offset])

        select_query = f"""
            SELECT
                {_READ_MODEL_COLUMNS},
                (dp.name ~* %s OR COALESCE(dp.name_translit ~* %s, FALSE)) AS exact_match,
                (dp.name_embedding <=> %s::vector) AS distance,
                COUNT(*) OVER() AS total_count
            {_READ_MODEL_JOINS}
            WHERE dp.name_embedding IS NOT NULL
              AND (
                    dp.name ~* %s
                    OR COALESCE(dp.name_translit ~* %s, FALSE)
                    OR (dp.name_embedding <=> %s::vector) <= {_MAX_COSINE_DISTANCE}
                  )
              {filters}
            {_SEARCH_ORDER_BY}
            LIMIT %s OFFSET %s
        """
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(select_query, params)
            rows = cursor.fetchall()
        if not rows:
            return [], 0
        total = int(rows[0][-1])
        # Column layout: read-model columns (0..17), exact_match (18), distance (19), total (20).
        items: list[DiscountedProductReadModel] = []
        for row in rows:
            item = _row_to_read_model(row)
            item["match_confidence"] = _confidence_from_distance(row[19])
            items.append(item)
        return items, total

    def __search_by_category_sync(
        self, category_uuid: str, offset: int, limit: int
    ) -> tuple[list[DiscountedProductReadModel], int]:
        # Most-confident matches first (smallest distance to the category prototype), with NULLs
        # last so any legacy uncategorised-distance rows sink; then cheapest, then a stable tie-break.
        select_query = f"""
            SELECT
                {_READ_MODEL_COLUMNS},
                dp.category_distance,
                COUNT(*) OVER() AS total_count
            {_READ_MODEL_JOINS}
            WHERE dp.category_uuid = %s
            ORDER BY dp.category_distance ASC NULLS LAST, dp.discounted_price ASC, dp.uuid ASC
            LIMIT %s OFFSET %s
        """
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(select_query, [category_uuid, limit, offset])
            rows = cursor.fetchall()
        if not rows:
            return [], 0
        total = int(rows[0][-1])
        # Column layout: read-model columns (0..17), category_distance (18), total (19).
        items: list[DiscountedProductReadModel] = []
        for row in rows:
            item = _row_to_read_model(row)
            if row[18] is not None:
                item["category_confidence"] = _confidence_from_distance(row[18])
            items.append(item)
        return items, total

    def __get_by_uuid_sync(self, uuid_: str) -> DiscountedProductReadModel:
        select_query = f"""
            SELECT {_READ_MODEL_COLUMNS}
            {_READ_MODEL_JOINS}
            WHERE dp.uuid = %s
        """
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(select_query, [uuid_])
            row = cursor.fetchone()
        if row is None:
            msg = f"Discounted product read model not found: {uuid_}"
            raise KeyError(msg)
        return _row_to_read_model(row)

    @staticmethod
    def __count_unembedded() -> int:
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM discounted_products WHERE name_embedding IS NULL")
            return int(cursor.fetchone()[0])

    @staticmethod
    def __fetch_unembedded(batch_size: int) -> list[tuple[str, str]]:
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT uuid, name
                FROM discounted_products
                WHERE name_embedding IS NULL
                ORDER BY uuid
                LIMIT %s
                """,
                [batch_size],
            )
            return [(str(row[0]), row[1]) for row in cursor.fetchall()]

    @staticmethod
    def __store_embeddings(uuids: list[str], vectors: list[list[float]]) -> None:
        cursor: CursorWrapper
        with connection.cursor() as cursor:
            cursor.executemany(
                "UPDATE discounted_products SET name_embedding = %s::vector WHERE uuid = %s",
                [(_vector_literal(vector), uuid_) for uuid_, vector in zip(uuids, vectors, strict=True)],
            )
