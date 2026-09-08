from app.embedding.base import EmbeddingModel
from app.retrieval.models import RetrievalResult
from app.vectorstore.qdrant_repository import QdrantRepository


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
        session_id: str | None = None,
    ) -> list[RetrievalResult]:

        query = query.strip()

        if not query:
            return []

        # 1. Embed query
        vector = self.embedding_model.embed([query])[0]

        # 2. Search vector database
        points = self.vector_store.search(
            vector=vector,
            limit=limit,
            document_id=document_id,
            session_id=session_id,
        )

        # 3. Convert DB result → application model
        results = []

        for point in points:
            payload = point.payload or {}

            results.append(
                RetrievalResult(
                    chunk_id=payload["chunk_id"],
                    document_id=payload["document_id"],
                    text=payload["text"],
                    score=point.score,
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
            )

        return results