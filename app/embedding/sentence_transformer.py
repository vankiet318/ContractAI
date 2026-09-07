from sentence_transformers import SentenceTransformer

from .base import EmbeddingModel


class SentenceTransformerEmbedding(EmbeddingModel):

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        batch_size: int = 32,
    ):
        self.model = SentenceTransformer(
            model_name,
            device=device,
        )

        self.batch_size = batch_size

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()