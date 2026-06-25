"""Minimal embedding server: sentence-transformers (PyTorch, CPU) behind an HTTP API.

Serves ``Metric-AI/armenian-text-embeddings-2-large`` (a multilingual E5 model fine-tuned for
Armenian). We run the published sentence-transformers weights directly because HuggingFace TEI's
Candle CPU backend segfaults on this model and the repo ships no ONNX for TEI's ORT backend.

The HTTP contract intentionally mirrors TEI's ``/embed`` so the application's embedding client
stays provider-agnostic: ``POST /embed`` with ``{"inputs": [...]}`` returns a top-level JSON
array of vectors, one per input, in order. The E5 ``query: ``/``passage: `` prefixes are added by
the caller, so this server embeds whatever text it receives verbatim.
"""

from __future__ import annotations

import os
import threading
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_MODEL_ID = os.environ.get("EMBEDDING_MODEL_ID", "Metric-AI/armenian-text-embeddings-2-large")

# Serializes ``encode`` across requests. This is a CPU model and PyTorch already uses every core
# for one batch, so letting concurrent requests encode in parallel only thrashes the CPU and
# spikes memory (each fights for all cores), making every request slower and risking client read
# timeouts. One batch at a time, using the whole CPU, is both faster and bounded in memory.
_encode_lock = threading.Lock()

# Holds the loaded model. Populated in the lifespan handler before the server accepts traffic, so
# ``/health`` only ever succeeds once the model is ready (which is what the container healthcheck
# and the app's startup gating rely on).
_state: dict[str, SentenceTransformer] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # On first boot this downloads the model into HF_HOME (the mounted /data volume); afterwards
    # it loads from cache. Either way it blocks startup until the model is usable.
    _state["model"] = SentenceTransformer(_MODEL_ID, device="cpu")
    try:
        yield
    finally:
        _state.clear()


app = FastAPI(lifespan=lifespan)


class EmbedRequest(BaseModel):
    inputs: str | list[str]
    # Accepted for TEI compatibility. ``normalize`` is honoured; ``truncate`` is implicit —
    # sentence-transformers always truncates to the model's max sequence length (512).
    normalize: bool = True
    truncate: bool = True


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/embed")
def embed(request: EmbedRequest) -> list[list[float]]:
    # Sync endpoint on purpose: ``encode`` is CPU-bound, so FastAPI runs it in its threadpool
    # rather than blocking the event loop. The lock then serializes the actual encoding so
    # concurrent requests queue instead of thrashing the CPU (see ``_encode_lock``).
    texts = [request.inputs] if isinstance(request.inputs, str) else request.inputs
    model = _state["model"]
    with _encode_lock:
        vectors = model.encode(texts, normalize_embeddings=request.normalize, convert_to_numpy=True)
    return vectors.tolist()
