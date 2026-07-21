"""Pydantic request/response schemas."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class DocumentOut(BaseModel):
    id: int
    source: str
    title: str
    num_chunks: int

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    document: DocumentOut


class QueryRequest(BaseModel):
    # Non-blank question: an empty string reaches the embeddings API and throws
    # BadRequestError ("input cannot be empty"), surfacing as a 500. Validate here
    # so bad input becomes a clean 422 instead.
    question: Annotated[str, Field(min_length=1)]
    # top_k must be >= 1: a negative value reaches Postgres as `LIMIT -1` and
    # raises InvalidRowCountInLimitClauseError (500). Cap at 50 for sanity.
    top_k: Annotated[int | None, Field(ge=1, le=50)] = None

    @field_validator("question")
    @classmethod
    def _question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank")
        return v.strip()


class Citation(BaseModel):
    document_id: int
    source: str
    chunk_idx: int
    snippet: str  # ~first 200 chars of the chunk


class RetrievedHit(BaseModel):
    document_id: int
    source: str
    chunk_idx: int
    score: float  # cosine distance (lower is better)
    content: str  # full passage text (lets clients + the eval judge inspect what was retrieved)


class QueryResponse(BaseModel):
    question: str
    answer: str
    retrieved: list[RetrievedHit]  # the top-k chunks actually retrieved
    citations: list[Citation]  # the subset the model chose to cite
