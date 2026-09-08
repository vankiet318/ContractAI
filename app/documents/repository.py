from app.db.models import DocumentORM
from app.db.session import get_db_session
from app.documents.models import Document, DocumentStatus


class DocumentRepository:

    def create(self, document: Document) -> None:
        with get_db_session() as db:
            db.add(
                DocumentORM(
                    id=document.document_id,
                    session_id=document.session_id,
                    filename=document.filename,
                    file_path=document.file_path,
                    status=document.status.value,
                    created_at=document.created_at,
                    error_message=document.error_message,
                )
            )

    def get(self, document_id: str) -> Document | None:
        with get_db_session() as db:
            row = db.get(DocumentORM, document_id)
            return self._to_domain(row) if row else None

    def list_all(self) -> list[Document]:
        with get_db_session() as db:
            rows = db.query(DocumentORM).all()
            return [self._to_domain(row) for row in rows]

    def list_by_session(self, session_id: str) -> list[Document]:
        with get_db_session() as db:
            rows = (
                db.query(DocumentORM)
                .filter(DocumentORM.session_id == session_id)
                .all()
            )
            return [self._to_domain(row) for row in rows]

    def update(self, document: Document) -> None:
        with get_db_session() as db:
            row = db.get(DocumentORM, document.document_id)

            if row is None:
                raise ValueError(
                    f"Document not found: {document.document_id}"
                )

            row.status = document.status.value
            row.error_message = document.error_message

    def delete(self, document_id: str) -> None:
        with get_db_session() as db:
            row = db.get(DocumentORM, document_id)
            if row is not None:
                db.delete(row)

    @staticmethod
    def _to_domain(row: DocumentORM) -> Document:
        return Document(
            document_id=row.id,
            session_id=row.session_id,
            filename=row.filename,
            file_path=row.file_path,
            status=DocumentStatus(row.status),
            created_at=row.created_at,
            error_message=row.error_message,
        )
