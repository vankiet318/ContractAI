from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.models import RetrievalResult
from app.retrieval.rrf import RRFFusion


class HybridRetriever:

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        bm25_retriever: BM25Retriever,
        rrf: RRFFusion,
    ):
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
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

        bm25_results = self.bm25_retriever.retrieve(
            query=query,
            limit=candidate_limit,
            session_id=session_id,
        )

        return self.rrf.fuse(
            result_lists=[
                dense_results,
                bm25_results,
            ],
            limit=limit,
        )