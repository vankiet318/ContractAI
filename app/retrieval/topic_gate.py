from abc import ABC, abstractmethod

from app.embedding.base import EmbeddingModel


class TopicGate(ABC):

    @abstractmethod
    def is_on_topic(self, query_vector: list[float]) -> bool:
        raise NotImplementedError


class AnchorTopicGate(TopicGate):
    """
    Decides whether a question is about the contract by comparing its
    dense vector with fixed example questions, before any search or
    reranking runs.

    A threshold on the best chunk score cannot do this: it depends on each
    contract's text (a chunk of table numbers makes "1+1 bằng bao nhiêu?"
    look relevant). The examples are the same for every contract.

    margin = best similarity to a contract example
             - best similarity to an off-topic example
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        contract_examples: list[str],
        off_topic_examples: list[str],
        min_margin: float,
    ):
        self.contract_vectors = embedding_model.embed(contract_examples)
        self.off_topic_vectors = embedding_model.embed(off_topic_examples)
        self.min_margin = min_margin

    def is_on_topic(self, query_vector: list[float]) -> bool:
        return self.margin(query_vector) >= self.min_margin

    def margin(self, query_vector: list[float]) -> float:
        return (
            best_similarity(query_vector, self.contract_vectors)
            - best_similarity(query_vector, self.off_topic_vectors)
        )


def best_similarity(vector: list[float], candidates: list[list[float]]) -> float:
    # Vectors are L2-normalized, so the dot product is the cosine similarity.
    return max(
        sum(a * b for a, b in zip(vector, candidate))
        for candidate in candidates
    )
