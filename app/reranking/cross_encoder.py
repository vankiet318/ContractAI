from sentence_transformers import CrossEncoder

from app.reranking.base import Reranker


class CrossEncoderReranker(Reranker):

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
    ):
        self.model = CrossEncoder(
            model_name,
            device=device,
        )

    def rerank(
        self,
        query: str,
        documents: list[str],
    ) -> list[float]:

        if not documents:
            return []

        pairs = [
            [query, document]
            for document in documents
        ]

        scores = self.model.predict(
            pairs,
            show_progress_bar=False,
        )

        return [
            float(score)
            for score in scores
        ]