from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    UploadFile,
)

from app.dependencies import document_service, indexing_service

router = APIRouter()

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def index_document(document_id: str, file_path: str) -> None:
    try:
        indexing_service.index(
            file_path=file_path,
            document_id=document_id,
        )

        document_service.mark_ready(document_id)

    except Exception as error:
        document_service.mark_failed(
            document_id=document_id,
            error_message=str(error),
        )


@router.post("")
async def upload_document(
    background_tasks: BackgroundTasks,
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

    document = document_service.create(
        document_id=document_id,
        filename=file.filename,
        file_path=str(file_path),
    )

    background_tasks.add_task(
        index_document,
        document_id,
        str(file_path),
    )

    return {
        "document_id": document.document_id,
        "filename": document.filename,
        "status": document.status,
    }


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
