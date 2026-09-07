from app.reranking.base import Reranker
from app.retrieval.models import RetrievalResult


class RerankingService:

    def __init__(
        self,
        reranker: Reranker,
    ):
        self.reranker = reranker

    def rerank(
        self,
        query: str,
        results: list[RetrievalResult],
        limit: int = 5,
    ) -> list[RetrievalResult]:

        if not results:
            return []

        documents = [
            result.text
            for result in results
        ]

        scores = self.reranker.rerank(
            query=query,
            documents=documents,
        )

        scored_results = []

        for result, score in zip(
            results,
            scores,
        ):
            scored_results.append(
                RetrievalResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    text=result.text,
                    score=score,
                    page_start=result.page_start,
                    page_end=result.page_end,
                    section_number=result.section_number,
                    section_title=result.section_title,
                    metadata=result.metadata,
                )
            )

        scored_results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return scored_results[:limit]