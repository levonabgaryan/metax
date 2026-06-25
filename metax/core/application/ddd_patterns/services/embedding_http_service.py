"""HTTP client for the embedding server (``metax-embeddings``).

Talks to the dedicated sentence-transformers service over its ``/embed`` endpoint (see
``embeddings_server/app.py``), which serves ``armenian-text-embeddings-2-large``. The endpoint
accepts a list of strings and returns one vector per input.

This model is *asymmetric*: it requires a ``query: `` prefix on search queries and a
``passage: `` prefix on indexed documents, even for non-English text. The prefixes are applied
here, in the one place that talks to the model, so call sites only pick ``embed_query`` vs
``embed_documents`` and never deal with prefixes directly.
"""

from __future__ import annotations

import asyncio
import logging
from typing import override

import httpx

from metax.core.application.ports.ddd_patterns.service.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# E5 instruction prefixes. The trailing space is part of the convention.
_QUERY_PREFIX = "query: "
_PASSAGE_PREFIX = "passage: "


class HttpEmbeddingService(EmbeddingService):
    def __init__(
        self,
        host: str,
        dimensions: int,
        concurrency: int = 6,
        timeout: float = 120.0,
        batch_size: int = 64,
    ) -> None:
        self._host = host.rstrip("/")
        self._dimensions = dimensions
        self._semaphore = asyncio.Semaphore(concurrency)
        self._timeout = timeout
        self._batch_size = batch_size

    @property
    @override
    def dimensions(self) -> int:
        return self._dimensions

    @override
    async def embed_query(self, text: str) -> list[float]:
        vectors = await self._embed([_QUERY_PREFIX + text])
        return vectors[0]

    @override
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._embed([_PASSAGE_PREFIX + text for text in texts])

    async def _embed(self, inputs: list[str]) -> list[list[float]]:
        chunks = [inputs[i : i + self._batch_size] for i in range(0, len(inputs), self._batch_size)]
        # Explicit read timeout: a cold model load keeps the connection open while producing no
        # bytes, which is exactly what `read` governs. Connect stays short.
        timeout = httpx.Timeout(self._timeout, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            results = await asyncio.gather(*[self._embed_chunk(client, chunk) for chunk in chunks])
        # Flatten the per-chunk results back into a single ordered list.
        return [vector for chunk_vectors in results for vector in chunk_vectors]

    async def _embed_chunk(self, client: httpx.AsyncClient, inputs: list[str]) -> list[list[float]]:
        async with self._semaphore:
            response = await client.post(
                f"{self._host}/embed",
                # ``truncate`` guards against the model's 512-token limit; ``normalize`` returns
                # unit vectors so cosine distance is the pgvector ``<=>`` operator's natural metric.
                json={"inputs": inputs, "truncate": True, "normalize": True},
            )
            response.raise_for_status()
            embeddings: list[list[float]] = response.json()
        if len(embeddings) != len(inputs):
            msg = f"Embedding server returned {len(embeddings)} embeddings for {len(inputs)} inputs"
            raise RuntimeError(msg)
        for embedding in embeddings:
            if len(embedding) != self._dimensions:
                msg = (
                    f"Embedding model returned dimension {len(embedding)}, "
                    f"expected {self._dimensions}"
                )
                raise RuntimeError(msg)
        return embeddings
