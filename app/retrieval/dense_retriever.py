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

        vector = self.embedding_model.embed([query])[0]

        return self.search(
            vector=vector,
            limit=limit,
            document_id=document_id,
            session_id=session_id,
        )

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> list[RetrievalResult]:

        points = self.vector_store.search_dense(
            vector=vector,
            limit=limit,
            document_id=document_id,
            session_id=session_id,
        )

        return [
            RetrievalResult.from_payload(
                payload=point.payload or {},
                score=point.score,
            )
            for point in points
        ]
