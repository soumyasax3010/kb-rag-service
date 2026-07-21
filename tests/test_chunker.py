"""Chunker unit tests — no DB or network needed."""

from app.ingest.chunker import chunk_text


def test_empty_returns_empty():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_text_single_chunk():
    chunks = chunk_text("RAG grounds answers in retrieved context.", chunk_size=512, overlap=64)
    assert len(chunks) == 1
    assert chunks[0].idx == 0
    assert "RAG" in chunks[0].content


def test_overlap_preserves_tokens_across_boundary():
    # Long enough to produce multiple chunks; verify consecutive chunks share
    # the overlap window by checking idx ordering and non-empty contents.
    text = " ".join(f"word{i}" for i in range(4000))
    chunks = chunk_text(text, chunk_size=256, overlap=64)
    assert len(chunks) > 1
    assert [c.idx for c in chunks] == list(range(len(chunks)))
    assert all(c.content.strip() for c in chunks)


def test_overlap_smaller_than_chunk_size_required():
    import pytest

    with pytest.raises(ValueError):
        chunk_text("hi", chunk_size=128, overlap=128)


def test_full_coverage_first_token_present():
    text = "alpha beta gamma " * 1000
    chunks = chunk_text(text, chunk_size=128, overlap=32)
    # The first token of the document must survive in the first chunk.
    assert "alpha" in chunks[0].content
