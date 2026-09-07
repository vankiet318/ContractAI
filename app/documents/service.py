from datetime import datetime
from app.documents.models import Document, DocumentStatus
from app.documents.repository import DocumentRepository


class DocumentService:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def create(
        self,
        document_id: str,
        filename: str,
        file_path: str,
    ) -> Document:

        document = Document(
            document_id=document_id,
            filename=filename,
            file_path=file_path,
            status=DocumentStatus.PROCESSING,
            created_at=datetime.now(),
        )

        self.repository.create(document)

        return document

    def get(self, document_id: str) -> Document | None:
        return self.repository.get(document_id)

    def mark_ready(self, document_id: str) -> None:
        document = self.repository.get(document_id)

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        document.status = DocumentStatus.READY

        self.repository.update(document)

    def mark_failed(
        self,
        document_id: str,
        error_message: str,
    ) -> None:

        document = self.repository.get(document_id)

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        document.status = DocumentStatus.FAILED
        document.error_message = error_message

        self.repository.update(document)