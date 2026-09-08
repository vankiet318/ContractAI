from pathlib import Path

from app.documents.service import DocumentService
from app.retrieval.bm25_index import BM25Index
from app.sessions.service import SessionService
from app.vectorstore.qdrant_repository import QdrantRepository


class SessionDeletionService:

    def __init__(
        self,
        session_service: SessionService,
        document_service: DocumentService,
        vector_store: QdrantRepository,
        bm25_index: BM25Index,
    ):
        self.session_service = session_service
        self.document_service = document_service
        self.vector_store = vector_store
        self.bm25_index = bm25_index

    def delete(self, session_id: str, user_id: str) -> None:

        session = self.session_service.get_owned(
            session_id=session_id,
            user_id=user_id,
        )

        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        documents = self.document_service.list_by_session(
            session_id
        )

        for document in documents:
            Path(document.file_path).unlink(missing_ok=True)

        self.vector_store.delete_by_session(session_id)

        self.bm25_index.delete(session_id)

        for document in documents:
            self.document_service.delete(document.document_id)

        self.session_service.delete(session_id)
