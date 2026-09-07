from abc import ABC, abstractmethod


class EmbeddingModel(ABC):

    @abstractmethod
    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """
        Convert texts into embedding vectors.
        """
        raise NotImplementedError