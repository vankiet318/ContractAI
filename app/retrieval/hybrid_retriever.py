from app.embedding.base import HybridEmbeddingModel
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.models import RetrievalResult
from app.retrieval.rrf import RRFFusion
from app.retrieval.sparse_retriever import SparseRetriever
from app.retrieval.topic_gate import TopicGate


class HybridRetriever:
    """
    Dense + sparse retrieval fused with RRF. The query is embedded once
    (one BGE-M3 pass yields both vectors) and each vector is searched
    against its own named vector in Qdrant.

    Off-topic questions return nothing, so the caller skips reranking and
    generation:
    - topic_gate rejects them from the query vector alone, before any
      search (e.g. "1+1 bằng bao nhiêu?");
    - min_dense_score rejects them when even the best dense match is
      below it. Keep it conservative; it depends on each contract's text.
    """

    def __init__(
        self,
        embedding_model: HybridEmbeddingModel,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever,
        rrf: RRFFusion,
        min_dense_score: float = 0.0,
        topic_gate: TopicGate | None = None,
    ):
        self.embedding_model = embedding_model
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.rrf = rrf
        self.min_dense_score = min_dense_score
        self.topic_gate = topic_gate

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

        if self.topic_gate and not self.topic_gate.is_on_topic(dense_vectors[0]):
            return []

        dense_results = self.dense_retriever.search(
            vector=dense_vectors[0],
            limit=candidate_limit,
            session_id=session_id,
        )

        if not self._has_related_match(dense_results):
            return []

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

    def _has_related_match(
        self,
        dense_results: list[RetrievalResult],
    ) -> bool:

        # Dense results are sorted by cosine similarity, best first.
        return bool(dense_results) and (
            dense_results[0].score >= self.min_dense_score
        )
