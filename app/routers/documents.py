"""Documents router: upload, list, delete."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.ingest.pipeline import delete_document, ingest_bytes, list_documents
from app.schemas import DocumentOut, IngestResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=IngestResponse, status_code=201)
async def upload_document(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    data = await file.read()
    try:
        doc = await ingest_bytes(session, data, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestResponse(document=DocumentOut.model_validate(doc))


@router.get("", response_model=list[DocumentOut])
async def get_documents(session: AsyncSession = Depends(get_session)):
    docs = await list_documents(session)
    return [DocumentOut.model_validate(d) for d in docs]


@router.delete("/{document_id}", status_code=204)
async def remove_document(document_id: int, session: AsyncSession = Depends(get_session)):
    deleted = await delete_document(session, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="document not found")
