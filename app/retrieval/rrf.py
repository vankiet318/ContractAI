from collections import defaultdict

from app.retrieval.models import RetrievalResult


class RRFFusion:

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        result_lists: list[list[RetrievalResult]],
        limit: int = 10,
    ) -> list[RetrievalResult]:

        scores = defaultdict(float)
        results_by_id: dict[str, RetrievalResult] = {}

        for results in result_lists:

            for rank, result in enumerate(results, start=1):

                chunk_id = result.chunk_id

                scores[chunk_id] += (
                    1.0 / (self.k + rank)
                )

                results_by_id[chunk_id] = result

        ranked_ids = sorted(
            scores,
            key=scores.get,
            reverse=True,
        )[:limit]

        fused_results = []

        for chunk_id in ranked_ids:

            result = results_by_id[chunk_id]

            fused_results.append(
                RetrievalResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    text=result.text,
                    score=scores[chunk_id],
                    page_start=result.page_start,
                    page_end=result.page_end,
                    section_number=result.section_number,
                    section_title=result.section_title,
                    metadata=result.metadata,
                )
            )

        return fused_results