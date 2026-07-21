"""Pydantic request/response schemas."""

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    source: str
    title: str
    num_chunks: int

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    document: DocumentOut


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None


class Citation(BaseModel):
    document_id: int
    source: str
    chunk_idx: int
    snippet: str  # ~first 200 chars of the chunk


class QueryResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
