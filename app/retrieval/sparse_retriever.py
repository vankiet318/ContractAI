from app.embedding.base import SparseEmbedding, SparseEmbeddingModel
from app.retrieval.models import RetrievalResult
from app.vectorstore.qdrant_repository import QdrantRepository


class SparseRetriever:
    """
    Keyword-style retrieval over the sparse (lexical weight) vectors
    stored in Qdrant. Replaces the old in-memory BM25 index: scores are
    the dot product of query and chunk token weights, so chunks sharing
    rare, high-weight tokens with the query (clause numbers, amounts,
    names) rank first.
    """

    def __init__(
        self,
        embedding_model: SparseEmbeddingModel,
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

        vector = self.embedding_model.embed_sparse([query])[0]

        return self.search(
            vector=vector,
            limit=limit,
            document_id=document_id,
            session_id=session_id,
        )

    def search(
        self,
        vector: SparseEmbedding,
        limit: int = 5,
        document_id: str | None = None,
        session_id: str | None = None,
    ) -> list[RetrievalResult]:

        points = self.vector_store.search_sparse(
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
