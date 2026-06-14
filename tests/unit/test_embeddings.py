from __future__ import annotations

from contextsmith_shared.embeddings import embed_text, term_overlap_score, vector_literal


def test_hashing_embedding_is_deterministic_and_normalized() -> None:
    first = embed_text("Resource lifecycle cleanup")
    second = embed_text("Resource lifecycle cleanup")
    assert first == second
    assert len(first) == 64
    assert any(value != 0 for value in first)
    norm = sum(value * value for value in first) ** 0.5
    assert 0.999 <= norm <= 1.001


def test_vector_literal_matches_pgvector_format() -> None:
    literal = vector_literal([0.5, -0.25])
    assert literal == "[0.50000000,-0.25000000]"


def test_term_overlap_score() -> None:
    assert term_overlap_score("resource cleanup", "cleanup old resource versions") == 1.0
    assert term_overlap_score("resource cleanup", "unrelated text") == 0.0
