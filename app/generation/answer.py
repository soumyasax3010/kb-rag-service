"""Answer generation: build a cited prompt, call the chat model, return answer text.

The prompt gives the model numbered context passages and instructs it to cite by
the passage number. The router maps those numbers back to concrete chunks.
"""

from openai import AsyncOpenAI

from app.config import settings
from app.retrieval.search import Hit

_client: AsyncOpenAI | None = None


def client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


SYSTEM_PROMPT = (
    "You are a precise knowledge-base assistant. Answer ONLY from the provided "
    "context passages. If the answer is not in the context, say you don't know. "
    "Cite every claim using the passage number in square brackets, e.g. [1]. "
    "Be concise."
)


def _build_context(hits: list[Hit]) -> str:
    parts = []
    for i, hit in enumerate(hits, start=1):
        parts.append(f"[{i}] (source: {hit.source})\n{hit.content}")
    return "\n\n".join(parts)


def _user_prompt(question: str, hits: list[Hit]) -> str:
    return (
        f"Context passages:\n{_build_context(hits)}\n\n"
        f"Question: {question}\n\nAnswer (cite passages as [n]):"
    )


async def generate_answer(question: str, hits: list[Hit]) -> str:
    if not hits:
        return "I don't know — no relevant context was found in the knowledge base."
    resp = await client().chat.completions.create(
        model=settings.chat_model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(question, hits)},
        ],
    )
    return resp.choices[0].message.content or ""
