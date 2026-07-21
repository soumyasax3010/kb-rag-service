"""Ingest pipeline: extract -> chunk -> embed -> persist."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.chunker import chunk_text
from app.ingest.loader import load_text
from app.models import Chunk, Document
from app.retrieval.embed import embed_texts


def _title_from(source: str) -> str:
    return source.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace("-", " ").replace("_", " ").title()


async def ingest_bytes(session: AsyncSession, data: bytes, source: str) -> Document:
    """Parse, chunk, embed, and store a single uploaded file."""
    text = load_text(data, source)
    pieces = chunk_text(text)
    if not pieces:
        raise ValueError(f"No text content extracted from {source!r}")

    doc = Document(source=source, title=_title_from(source), num_chunks=len(pieces))
    session.add(doc)
    await session.flush()  # populate doc.id

    vectors = await embed_texts([p.content for p in pieces])
    session.add_all(
        Chunk(
            document_id=doc.id,
            chunk_idx=p.idx,
            content=p.content,
            embedding=vec,
        )
        for p, vec in zip(pieces, vectors, strict=True)
    )
    await session.commit()
    await session.refresh(doc)
    return doc


async def delete_document(session: AsyncSession, document_id: int) -> bool:
    doc = await session.get(Document, document_id)
    if doc is None:
        return False
    await session.execute(delete(Chunk).where(Chunk.document_id == document_id))
    await session.delete(doc)
    await session.commit()
    return True


async def list_documents(session: AsyncSession) -> list[Document]:
    result = await session.execute(select(Document).order_by(Document.id))
    return list(result.scalars().all())
