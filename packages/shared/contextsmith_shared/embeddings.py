from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

EMBEDDING_DIMENSIONS = 64
DEFAULT_EMBEDDING_PROVIDER = "hashing"
DEFAULT_EMBEDDING_MODEL = "contextsmith-hashing-v1"
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str = DEFAULT_EMBEDDING_PROVIDER
    model: str = DEFAULT_EMBEDDING_MODEL
    dimensions: int = EMBEDDING_DIMENSIONS


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def embed_text(text: str, *, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Return a deterministic local embedding for dev/test retrieval.

    This is intentionally not a semantic model. It is a zero-dependency hashing
    provider that exercises the same storage/retrieval path as future HF/vLLM/
    SGLang providers while keeping local CI fast and offline. Tokens are hashed
    into a signed bag-of-words vector and L2-normalized so pgvector cosine
    distance is meaningful enough for tests and lexical-hybrid fallback.
    """
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    vector = [0.0] * dimensions
    tokens = tokenize(text)
    if not tokens and text:
        tokens = [text.lower()[:128]]
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def vector_literal(vector: list[float]) -> str:
    """Serialize a vector for pgvector CAST(:value AS vector)."""
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def term_overlap_score(query: str, content: str) -> float:
    """Simple deterministic dev reranker score in [0, 1]."""
    query_terms = set(tokenize(query))
    if not query_terms:
        return 0.0
    content_terms = set(tokenize(content))
    if not content_terms:
        return 0.0
    return len(query_terms & content_terms) / len(query_terms)
