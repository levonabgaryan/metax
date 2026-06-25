from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    """Turns text into dense vectors for semantic (vector) search.

    Implementations must return vectors of a fixed dimension (see ``dimensions``) so the
    pgvector column they are stored in stays consistent.

    The query/document split is part of the contract because the embedding model is
    *asymmetric* (the multilingual E5 family, which the Armenian model is built on): it
    expects a ``query: `` instruction prefix on search queries and a ``passage: `` prefix
    on the documents being indexed. Embedding a query as a document (or vice versa)
    silently degrades retrieval quality, so the distinction is encoded in the interface
    rather than left to call sites to remember.
    """

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """The length of every embedding vector this service produces."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single search query (prefixed as a query)."""

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents to be indexed; the result preserves input order."""
