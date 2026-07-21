"""OpenAI embeddings client.

Thin wrapper so the only place that knows about OpenAI for embeddings is this
file + ``app/config.py``. Swapping providers = editing these two files.
"""

from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
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
