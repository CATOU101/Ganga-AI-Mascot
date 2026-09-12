"""Lightweight local embedding functions for the prototype Brain."""

from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Any

# Configure conservative ONNX & OpenMP thread limits before C-extension libraries load
_ORT_THREADS = os.getenv("GANGA_BRAIN_ORT_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", _ORT_THREADS)
os.environ.setdefault("ONNXRUNTIME_SESSION_THREAD_POOL_SIZE", _ORT_THREADS)
os.environ.setdefault("OPENBLAS_NUM_THREADS", _ORT_THREADS)
os.environ.setdefault("MKL_NUM_THREADS", _ORT_THREADS)
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", _ORT_THREADS)
os.environ.setdefault("NUMEXPR_NUM_THREADS", _ORT_THREADS)


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_EMBEDDING_CACHE: dict[str, Any] = {}


class LocalHashEmbedding:
    """Deterministic bag-of-words hashing embedding baseline.

    This avoids paid APIs and large model downloads while keeping the prototype
    reproducible. It is intentionally a baseline, not a final semantic model.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions
        self.name = "local-hash-embedding-v1"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            return vector
        return [value / norm for value in vector]


class ONNXSemanticEmbedding:
    """Local ONNX semantic embedding model (all-MiniLM-L6-v2).

    Uses ChromaDB's native ONNX MiniLM model running locally on CPU.
    Requires no paid API keys and produces 384-dimensional dense semantic vectors.
    """

    def __init__(self, ort_threads: int = 2) -> None:
        str_threads = str(ort_threads)
        os.environ.setdefault("OMP_NUM_THREADS", str_threads)
        os.environ.setdefault("ONNXRUNTIME_SESSION_THREAD_POOL_SIZE", str_threads)
        os.environ.setdefault("OPENBLAS_NUM_THREADS", str_threads)
        os.environ.setdefault("MKL_NUM_THREADS", str_threads)
        os.environ.setdefault("VECLIB_MAXIMUM_THREADS", str_threads)
        os.environ.setdefault("NUMEXPR_NUM_THREADS", str_threads)

        import chromadb.utils.embedding_functions as ef

        self._func = ef.DefaultEmbeddingFunction()
        self.name = "onnx-semantic-embedding-v1"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        res = self._func(texts)
        return [[float(x) for x in vec] for vec in res]

    def embed_query(self, text: str) -> list[float]:
        res = self._func([text])
        return [float(x) for x in res[0]]


def get_embedding_function(provider: str = "semantic", dimensions: int = 384, ort_threads: int = 2):
    provider_clean = (provider or "semantic").lower().strip()
    cache_key = f"{provider_clean}:{dimensions}:{ort_threads}"

    if cache_key in _EMBEDDING_CACHE:
        return _EMBEDDING_CACHE[cache_key]

    if provider_clean in ("semantic", "onnx", "default"):
        instance = ONNXSemanticEmbedding(ort_threads=ort_threads)
    elif provider_clean in ("local-hash", "hash", "baseline"):
        instance = LocalHashEmbedding(dimensions)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")

    _EMBEDDING_CACHE[cache_key] = instance
    return instance
