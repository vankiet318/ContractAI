from pathlib import Path

from app.documents.service import DocumentService
from app.vectorstore.qdrant_repository import QdrantRepository


class DocumentDeletionService:

    def __init__(
        self,
        document_service: DocumentService,
        vector_store: QdrantRepository,
    ):
        self.document_service = document_service
        self.vector_store = vector_store

    def delete(self, document_id: str, session_id: str) -> None:

        document = self.document_service.get(document_id)

        if document is None or document.session_id != session_id:
            raise ValueError(f"Document not found: {document_id}")

        Path(document.file_path).unlink(missing_ok=True)

        self.vector_store.delete_by_document(document_id)

        self.document_service.delete(document_id)
