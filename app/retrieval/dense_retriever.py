from dataclasses import dataclass
from typing import Any

from app.embedding.base import EmbeddingModel
from app.vectorstore.qdrant_repository import (
    QdrantRepository,
)


@dataclass
class RetrievalResult:

    chunk_id: str
    text: str

    score: float

    document_id: str

    page_start: int
    page_end: int

    section_number: str | None
    section_title: str | None

    metadata: dict[str, Any]

class DenseRetriever:

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_store: QdrantRepository,
    ):
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        document_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[RetrievalResult]:

        query_vector = (
            self.embedding_model.embed(
                [query]
            )[0]
        )

        results = self.vector_store.search(
            vector=query_vector,
            limit=limit,
            document_id=document_id,
            workspace_id=workspace_id,
        )

        return [
            self._convert_result(result)
            for result in results
        ]

    @staticmethod
    def _convert_result(
        result,
    ) -> RetrievalResult:

        payload = result.payload or {}

        return RetrievalResult(
            chunk_id=payload["chunk_id"],
            text=payload["text"],
            score=result.score,
            document_id=payload["document_id"],
            page_start=payload["page_start"],
            page_end=payload["page_end"],
            section_number=payload.get(
                "section_number"
            ),
            section_title=payload.get(
                "section_title"
            ),
            metadata=payload.get(
                "metadata",
                {},
            ),
        )