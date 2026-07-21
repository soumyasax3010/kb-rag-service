"""Vector search: embed a query, return top-k chunks via pgvector cosine distance.

Uses the ``<=>`` (cosine distance) operator against the HNSW index created in
the migration. Returns joined Document.source so citations can name the file.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Chunk, Document
from app.retrieval.embed import embed_query


@dataclass
class Hit:
    chunk_id: int
    document_id: int
    source: str
    chunk_idx: int
    content: str
    score: float  # cosine distance (lower is better)


async def search(session: AsyncSession, question: str, top_k: int | None = None) -> list[Hit]:
    # Clamp even if the API validated: internal callers (e.g. evals) may bypass it,
    # and `LIMIT -1` raises InvalidRowCountInLimitClauseError in Postgres.
    k = top_k or settings.top_k
    k = max(1, min(k, 50))
    query_vec = await embed_query(question)

    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Document.source,
            Chunk.chunk_idx,
            Chunk.content,
            Chunk.embedding.cosine_distance(query_vec).label("distance"),
        )
        .join(Document, Document.id == Chunk.document_id)
        .order_by("distance")
        .limit(k)
    )
    rows = (await session.execute(stmt)).all()
    return [
        Hit(
            chunk_id=r.id,
            document_id=r.document_id,
            source=r.source,
            chunk_idx=r.chunk_idx,
            content=r.content,
            score=float(r.distance),
        )
        for r in rows
    ]
