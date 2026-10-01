from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass
class ConversationTurn:
    question: str
    answer: str


class LLM(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
        history: list[ConversationTurn] | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        history: list[ConversationTurn] | None = None,
    ) -> Iterator[str]:
        """
        Yield the answer as text fragments, in order, as they are produced.
        """
        raise NotImplementedError
