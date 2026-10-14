import logging
from concurrent.futures import ThreadPoolExecutor

from app.documents.models import PROCESSING_FAILED_MESSAGE, Document
from app.documents.service import DocumentService
from app.ingestion.indexing_service import DocumentIndexingService
from app.vectorstore.qdrant_repository import QdrantRepository

logger = logging.getLogger(__name__)


class BackgroundIndexer:
    """
    Indexes uploaded documents on worker threads, so an upload returns as
    soon as the file is saved and the document stays PROCESSING until its
    worker marks it READY or FAILED.

    Indexing is CPU-heavy (embedding); a few workers keep a burst of uploads
    from starving the queries running on the same machine. Extra uploads
    wait in the executor's queue.
    """

    def __init__(
        self,
        indexing_service: DocumentIndexingService,
        document_service: DocumentService,
        vector_store: QdrantRepository,
        max_workers: int,
    ):
        self.indexing_service = indexing_service
        self.document_service = document_service
        self.vector_store = vector_store
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="indexing",
        )

    def submit(self, document: Document) -> None:
        self.executor.submit(self.index, document)

    def index(self, document: Document) -> None:
        try:
            self.indexing_service.index(
                file_path=document.file_path,
                document_id=document.document_id,
                session_id=document.session_id,
            )
        except Exception:
            logger.exception(
                "Indexing failed for document %s", document.document_id
            )
            self._mark_failed(document)
            return

        try:
            self.document_service.mark_ready(document.document_id)
        except ValueError:
            # Deleted while it was being indexed: the deletion removed the
            # vectors that existed then, not the ones written since.
            self.vector_store.delete_by_document(document.document_id)

    def _mark_failed(self, document: Document) -> None:
        try:
            self.document_service.mark_failed(
                document_id=document.document_id,
                error_message=PROCESSING_FAILED_MESSAGE,
            )
        except ValueError:
            pass  # Deleted while it was being indexed.
