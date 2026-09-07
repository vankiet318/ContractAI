from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)
from starlette.concurrency import run_in_threadpool

from app.dependencies import document_service, indexing_service

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    document_id = str(uuid4())

    file_path = (
        UPLOAD_DIR
        / f"{document_id}.pdf"
    )

    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    document_service.create(
        document_id=document_id,
        filename=file.filename,
        file_path=str(file_path),
    )

    try:
        await run_in_threadpool(
            indexing_service.index,
            file_path=str(file_path),
            document_id=document_id,
        )

        document = document_service.mark_ready(document_id)

    except Exception as error:
        document = document_service.mark_failed(
            document_id=document_id,
            error_message=str(error),
        )

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "status": document.status,
        "error_message": document.error_message,
    }


@router.get("")
def list_documents():

    documents = document_service.list_all()

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


@router.get("/{document_id}")
def get_document(document_id: str):

    document = document_service.get(
        document_id
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "status": document.status,
        "error_message": document.error_message,
    }
