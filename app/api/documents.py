import logging
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from app.documents.deletion_service import DocumentDeletionService
from app.documents.models import PROCESSING_FAILED_MESSAGE, Document
from app.documents.service import DocumentService
from app.ingestion.indexing_service import DocumentIndexingService
from app.sessions.models import ChatSession

logger = logging.getLogger(__name__)

UPLOAD_CHUNK_BYTES = 1024 * 1024


class UploadTooLargeError(Exception):
    pass


async def save_upload(
    file: UploadFile,
    destination: Path,
    max_bytes: int,
) -> None:
    """
    Stream the upload to disk, stopping as soon as it exceeds max_bytes so
    an oversized file never fills the disk.
    """
    written = 0

    with destination.open("wb") as buffer:
        while chunk := await file.read(UPLOAD_CHUNK_BYTES):
            written += len(chunk)

            if written > max_bytes:
                break

            buffer.write(chunk)

    if written > max_bytes:
        destination.unlink(missing_ok=True)
        raise UploadTooLargeError()


def _get_owned_document(
    document_service: DocumentService,
    document_id: str,
    session_id: str,
) -> Document:

    document = document_service.get(document_id)

    if document is None or document.session_id != session_id:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


def create_documents_router(
    document_service: DocumentService,
    indexing_service: DocumentIndexingService,
    deletion_service: DocumentDeletionService,
    get_owned_session: Callable[..., ChatSession],
    upload_dir: Path,
    max_upload_mb: int,
) -> APIRouter:

    router = APIRouter()

    @router.post("/{session_id}/documents")
    async def upload_document(
        session_id: str,
        file: UploadFile = File(...),
        session: ChatSession = Depends(get_owned_session),
    ):
        filename = file.filename or ""

        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported",
            )

        document_id = str(uuid4())

        file_path = (
            upload_dir
            / f"{document_id}.pdf"
        )

        try:
            await save_upload(
                file=file,
                destination=file_path,
                max_bytes=max_upload_mb * 1024 * 1024,
            )
        except UploadTooLargeError:
            raise HTTPException(
                status_code=413,
                detail=f"File vượt quá giới hạn {max_upload_mb} MB.",
            )

        document_service.create(
            document_id=document_id,
            session_id=session_id,
            filename=filename,
            file_path=str(file_path),
        )

        try:
            await run_in_threadpool(
                indexing_service.index,
                file_path=str(file_path),
                document_id=document_id,
                session_id=session_id,
            )

            document = document_service.mark_ready(document_id)

        except Exception:
            logger.exception("Indexing failed for document %s", document_id)
            document = document_service.mark_failed(
                document_id=document_id,
                error_message=PROCESSING_FAILED_MESSAGE,
            )

        return {
            "document_id": document.document_id,
            "filename": document.filename,
            "status": document.status,
            "error_message": document.error_message,
        }

    @router.get("/{session_id}/documents")
    def list_documents(
        session_id: str,
        session: ChatSession = Depends(get_owned_session),
    ):
        documents = document_service.list_by_session(session_id)

        return [
            {
                "document_id": document.document_id,
                "filename": document.filename,
                "status": document.status,
                "created_at": document.created_at,
                "error_message": document.error_message,
            }
            for document in documents
        ]

    @router.get("/{session_id}/documents/{document_id}")
    def get_document(
        session_id: str,
        document_id: str,
        session: ChatSession = Depends(get_owned_session),
    ):
        document = _get_owned_document(
            document_service, document_id, session_id
        )

        return {
            "document_id": document.document_id,
            "filename": document.filename,
            "status": document.status,
            "error_message": document.error_message,
        }

    @router.get("/{session_id}/documents/{document_id}/file")
    def get_document_file(
        session_id: str,
        document_id: str,
        session: ChatSession = Depends(get_owned_session),
    ):
        document = _get_owned_document(
            document_service, document_id, session_id
        )

        return FileResponse(
            document.file_path,
            media_type="application/pdf",
            filename=document.filename,
        )

    @router.delete(
        "/{session_id}/documents/{document_id}",
        status_code=204,
    )
    def delete_document(
        session_id: str,
        document_id: str,
        session: ChatSession = Depends(get_owned_session),
    ):
        _get_owned_document(document_service, document_id, session_id)

        try:
            deletion_service.delete(
                document_id=document_id,
                session_id=session_id,
            )
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail="Document not found",
            )

    return router
