"""
Rebuild the Qdrant collection from the uploaded PDFs.

Needed once after switching to dense + sparse vectors, because the old
collection only has a single unnamed dense vector. Every READY document
in Postgres is re-indexed from its stored file; documents that fail are
marked FAILED so the UI shows them.

Run inside the backend container:
    docker compose exec backend python -m app.scripts.reindex
"""

from pathlib import Path

from app.dependencies import (
    document_service,
    indexing_service,
    vector_store,
)
from app.documents.models import DocumentStatus


def main() -> None:

    documents = [
        document
        for document in document_service.list_all()
        if document.status == DocumentStatus.READY
    ]

    print(f"Dropping collection '{vector_store.collection_name}'")
    vector_store.delete_collection()

    for document in documents:

        if not Path(document.file_path).is_file():
            document_service.mark_failed(
                document_id=document.document_id,
                error_message="File missing during reindex",
            )
            print(f"MISSING  {document.filename}")
            continue

        try:
            chunk_count = indexing_service.index(
                file_path=document.file_path,
                document_id=document.document_id,
                session_id=document.session_id,
            )
        except Exception as error:
            document_service.mark_failed(
                document_id=document.document_id,
                error_message=str(error),
            )
            print(f"FAILED   {document.filename}: {error}")
            continue

        print(f"OK       {document.filename} ({chunk_count} chunks)")

    print(f"Reindexed {len(documents)} documents")


if __name__ == "__main__":
    main()
