from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SparseEmbedding:
    indices: list[int]
    values: list[float]


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


class SparseEmbeddingModel(ABC):

    @abstractmethod
    def embed_sparse(
        self,
        texts: list[str],
    ) -> list[SparseEmbedding]:
        """
        Convert texts into sparse (token id -> weight) vectors.
        """
        raise NotImplementedError
