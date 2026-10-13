from concurrent.futures import ThreadPoolExecutor

from sentence_transformers import CrossEncoder

from app.reranking.base import Reranker


class CrossEncoderReranker(Reranker):
    """
    Scores each (query, document) pair on its own: in a shared batch every
    pair is padded to the longest one, which on CPU roughly tripled the
    work for typical chunks. Pairs run on a thread pool shared by all
    requests, so concurrent queries never use more than `workers` model
    calls at once. Scores are the same as batched scoring.
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        workers: int = 4,
    ):
        self.model = CrossEncoder(
            model_name,
            device=device,
        )

        self.executor = ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="reranker",
        )

    def rerank(
        self,
        query: str,
        documents: list[str],
    ) -> list[float]:

        if not documents:
            return []

        return list(
            self.executor.map(
                lambda document: self._score(query, document),
                documents,
            )
        )

    def _score(
        self,
        query: str,
        document: str,
    ) -> float:

        scores = self.model.predict(
            [[query, document]],
            batch_size=1,
            show_progress_bar=False,
        )

        return float(scores[0])
