from app.embedding.base import HybridEmbeddingModel
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.models import RetrievalResult
from app.retrieval.rrf import RRFFusion
from app.retrieval.sparse_retriever import SparseRetriever


class HybridRetriever:
    """
    Dense + sparse retrieval fused with RRF. The query is embedded once
    (one BGE-M3 pass yields both vectors) and each vector is searched
    against its own named vector in Qdrant.
    """

    def __init__(
        self,
        embedding_model: HybridEmbeddingModel,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever,
        rrf: RRFFusion,
    ):
        self.embedding_model = embedding_model
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.rrf = rrf

    def retrieve(
        self,
        query: str,
        session_id: str,
        limit: int = 5,
        candidate_limit: int = 10,
    ) -> list[RetrievalResult]:

        query = query.strip()

        if not query:
            return []

        dense_vectors, sparse_vectors = self.embedding_model.embed_hybrid(
            [query]
        )

        dense_results = self.dense_retriever.search(
            vector=dense_vectors[0],
            limit=candidate_limit,
            session_id=session_id,
        )

        sparse_results = self.sparse_retriever.search(
            vector=sparse_vectors[0],
            limit=candidate_limit,
            session_id=session_id,
        )

        return self.rrf.fuse(
            result_lists=[
                dense_results,
                sparse_results,
            ],
            limit=limit,
        )
