"""Query router: retrieve chunks, generate a cited answer."""

import re

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.generation.answer import generate_answer
from app.retrieval.search import search
from app.schemas import Citation, QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["query"])

# Matches "[1]", "[2]", possibly several in one answer.
_CITE_RE = re.compile(r"\[(\d+)\]")


@router.post("", response_model=QueryResponse)
async def query(req: QueryRequest, session: AsyncSession = Depends(get_session)):
    hits = await search(session, req.question, top_k=req.top_k)

    answer = await generate_answer(req.question, hits)

    # Map the [n] markers the model emitted to the corresponding retrieved chunk.
    cited_indices = {int(n) for n in _CITE_RE.findall(answer)}
    citations: list[Citation] = []
    for n in sorted(cited_indices):
        if 1 <= n <= len(hits):
            hit = hits[n - 1]
            citations.append(
                Citation(
                    document_id=hit.document_id,
                    source=hit.source,
                    chunk_idx=hit.chunk_idx,
                    snippet=hit.content[:200],
                )
            )

    return QueryResponse(question=req.question, answer=answer, citations=citations)
