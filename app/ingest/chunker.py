"""Token-based chunking with overlap.

Uses tiktoken to split on token boundaries so chunks stay within model context
budgets and overlap preserves context across boundaries. Pure function → easy
to unit-test with no DB or network.
"""

from dataclasses import dataclass

import tiktoken

from app.config import settings


@dataclass
class Chunk:
    idx: int
    content: str


def chunk_text(
    text: str,
    chunk_size: int = settings.chunk_size_tokens,
    overlap: int = settings.chunk_overlap_tokens,
    encoding_name: str = "cl100k_base",
) -> list[Chunk]:
    """Split ``text`` into overlapping token windows, decoded back to strings.

    A step of ``chunk_size - overlap`` advances the window each iteration so
    every token (after the first window) appears in at least two chunks,
    preventing context loss at boundaries.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")

    text = text.strip()
    if not text:
        return []

    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    if not tokens:
        return []

    step = chunk_size - overlap
    chunks: list[Chunk] = []
    start = 0
    idx = 0
    n = len(tokens)
    while start < n:
        end = min(start + chunk_size, n)
        piece = enc.decode(tokens[start:end])
        if piece.strip():
            chunks.append(Chunk(idx=idx, content=piece))
            idx += 1
        if end == n:
            break
        start += step
    return chunks
