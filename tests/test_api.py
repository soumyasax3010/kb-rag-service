"""API smoke test: health and document listing endpoints (no DB writes)."""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_query_validates_required_question():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/query", json={})
    assert resp.status_code == 422


async def test_query_rejects_blank_question():
    # Empty/whitespace question used to reach the embeddings API and throw 500.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/query", json={"question": "   "})
    assert resp.status_code == 422


async def test_query_rejects_negative_top_k():
    # Negative top_k used to reach Postgres as `LIMIT -1` and throw 500.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/query", json={"question": "hi", "top_k": -1})
    assert resp.status_code == 422


async def test_query_rejects_zero_top_k():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post("/query", json={"question": "hi", "top_k": 0})
    assert resp.status_code == 422
