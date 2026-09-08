from datetime import datetime
from app.documents.models import Document, DocumentStatus
from app.documents.repository import DocumentRepository


class DocumentService:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def create(
        self,
        document_id: str,
        session_id: str,
        filename: str,
        file_path: str,
    ) -> Document:

        document = Document(
            document_id=document_id,
            session_id=session_id,
            filename=filename,
            file_path=file_path,
            status=DocumentStatus.PROCESSING,
            created_at=datetime.now(),
        )

        self.repository.create(document)

        return document

    def get(self, document_id: str) -> Document | None:
        return self.repository.get(document_id)

    def list_all(self) -> list[Document]:
        return sorted(
            self.repository.list_all(),
            key=lambda document: document.created_at,
            reverse=True,
        )

    def list_by_session(self, session_id: str) -> list[Document]:
        return sorted(
            self.repository.list_by_session(session_id),
            key=lambda document: document.created_at,
            reverse=True,
        )

    def delete(self, document_id: str) -> None:
        self.repository.delete(document_id)

    def mark_ready(self, document_id: str) -> Document:
        document = self.repository.get(document_id)

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        document.status = DocumentStatus.READY

        self.repository.update(document)

        return document

    def mark_failed(
        self,
        document_id: str,
        error_message: str,
    ) -> Document:

        document = self.repository.get(document_id)

        if document is None:
            raise ValueError(
                f"Document not found: {document_id}"
            )

        document.status = DocumentStatus.FAILED
        document.error_message = error_message

        self.repository.update(document)

        return document