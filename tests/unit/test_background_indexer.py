from datetime import datetime
from types import SimpleNamespace

from app.documents.indexing_runner import BackgroundIndexer
from app.documents.models import Document, DocumentStatus

DOCUMENT = Document(
    document_id="d1",
    session_id="s1",
    filename="hop-dong.pdf",
    file_path="/tmp/d1.pdf",
    status=DocumentStatus.PROCESSING,
    created_at=datetime(2026, 10, 14),
)


class FakeDocumentService:

    def __init__(self, exists=True):
        self.exists = exists
        self.ready = []
        self.failed = []

    def mark_ready(self, document_id):
        if not self.exists:
            raise ValueError(document_id)
        self.ready.append(document_id)

    def mark_failed(self, document_id, error_message):
        if not self.exists:
            raise ValueError(document_id)
        self.failed.append(document_id)


def build(index, document_service):
    deleted_vectors = []

    indexer = BackgroundIndexer(
        indexing_service=SimpleNamespace(index=index),
        document_service=document_service,
        vector_store=SimpleNamespace(delete_by_document=deleted_vectors.append),
        max_workers=1,
    )

    return indexer, deleted_vectors


def test_indexed_document_is_marked_ready():
    documents = FakeDocumentService()
    indexer, _ = build(lambda **kwargs: None, documents)

    indexer.index(DOCUMENT)

    assert documents.ready == ["d1"]


def test_indexing_error_marks_document_failed():
    def index(**kwargs):
        raise RuntimeError("broken pdf")

    documents = FakeDocumentService()
    indexer, _ = build(index, documents)

    indexer.index(DOCUMENT)

    assert documents.failed == ["d1"]
    assert documents.ready == []


def test_vectors_of_document_deleted_while_indexing_are_removed():
    indexer, deleted_vectors = build(
        lambda **kwargs: None,
        FakeDocumentService(exists=False),
    )

    indexer.index(DOCUMENT)

    assert deleted_vectors == ["d1"]


def test_failure_of_document_deleted_while_indexing_is_ignored():
    def index(**kwargs):
        raise FileNotFoundError("file removed by the deletion")

    indexer, _ = build(index, FakeDocumentService(exists=False))

    indexer.index(DOCUMENT)


def test_submit_runs_indexing_in_the_background():
    documents = FakeDocumentService()
    indexer, _ = build(lambda **kwargs: None, documents)

    indexer.submit(DOCUMENT)
    indexer.executor.shutdown(wait=True)

    assert documents.ready == ["d1"]
