from abc import ABC, abstractmethod
from dataclasses import dataclass


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