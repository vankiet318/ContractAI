from app.documents.models import Document


class DocumentRepository:

    def __init__(self):
        self._documents: dict[str, Document] = {}

    def create(self, document: Document) -> None:
        self._documents[document.document_id] = document

    def get(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    def update(self, document: Document) -> None:
        self._documents[document.document_id] = document

    def list_all(self) -> list[Document]:
        return list(self._documents.values())