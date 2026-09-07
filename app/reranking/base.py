from abc import ABC, abstractmethod


class Reranker(ABC):

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[str],
    ) -> list[float]:
        raise NotImplementedError