"""Embeddings client.

Uses the OpenAI SDK against any OpenAI-compatible endpoint (set
``OPENAI_BASE_URL`` for Fireworks / local). Swapping providers = editing
``app/config.py`` and this file only.
"""

from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning one vector per input (in order)."""
    if not texts:
        return []
    resp = await client().embeddings.create(model=settings.embed_model, input=texts)
    return [d.embedding for d in sorted(resp.data, key=lambda x: x.index)]


async def embed_query(text: str) -> list[float]:
    vecs = await embed_texts([text])
    return vecs[0]
