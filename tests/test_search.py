"""Integration test: ingest a fixture doc, query, expect the right doc retrieved.

Requires a running Postgres+pgvector (docker compose up db) and OPENAI_API_KEY.
Skips otherwise so unit runs stay green without infra.
"""

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.db import Base, engine
from app.main import app

CORPUS = Path(__file__).resolve().parent.parent / "sample_corpus"

pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="needs OPENAI_API_KEY",
)


@pytest.fixture(scope="session")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    # ingest one sample doc via the app's own pipeline
    overview = (CORPUS / "01-rag-overview.md").read_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/documents",
            files={"file": ("01-rag-overview.md", overview, "text/markdown")},
        )
        assert resp.status_code == 201, f"ingest failed: {resp.text}"
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio(loop_scope="session")
async def test_query_retrieves_overview_doc(setup_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(
            "/query", json={"question": "What are the three stages of RAG?", "top_k": 5}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert any("01-rag-overview" in h["source"] for h in body["retrieved"])
