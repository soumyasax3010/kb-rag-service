"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.ingest.pipeline import ingest_bytes
from app.models import Document
from app.routers import documents, query

SAMPLE_CORPUS = Path(__file__).resolve().parent.parent / "sample_corpus"


async def _seed_if_needed(session: AsyncSession) -> None:
    """On an empty DB, ingest the bundled sample corpus so the demo just works.

    Idempotent: only ingests sample docs whose source filename isn't already
    present, so cold restarts on the demo host don't duplicate or re-embed.
    """
    existing = {row[0] for row in (await session.execute(select(Document.source))).all()}
    for f in sorted(SAMPLE_CORPUS.glob("*.md")):
        if f.name in existing:
            continue
        try:
            await ingest_bytes(session, f.read_bytes(), f.name)
        except Exception as exc:  # noqa: BLE001 — log and continue so startup is resilient
            print(f"[seed] failed to ingest {f.name}: {exc}")


@asynccontextmanager
async def lifespan(app):  # type: ignore[no-untyped-def]
    async with SessionLocal() as session:
        await _seed_if_needed(session)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="KB RAG Service",
        description=(
            "Ingest documents, ask questions, get cited answers (pgvector + OpenAI-compatible LLM)."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(documents.router)
    app.include_router(query.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
