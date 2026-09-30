from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.models import RetrievalResult
from app.retrieval.rrf import RRFFusion
from app.retrieval.sparse_retriever import SparseRetriever


class HybridRetriever:

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever,
        rrf: RRFFusion,
    ):
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

        dense_results = self.dense_retriever.retrieve(
            query=query,
            limit=candidate_limit,
            session_id=session_id,
        )

        sparse_results = self.sparse_retriever.retrieve(
            query=query,
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