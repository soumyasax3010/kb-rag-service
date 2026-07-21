"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.routers import documents, query


def create_app() -> FastAPI:
    app = FastAPI(
        title="KB RAG Service",
        description="Ingest documents, ask questions, get cited answers (pgvector + OpenAI).",
        version="0.1.0",
    )
    app.include_router(documents.router)
    app.include_router(query.router)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
