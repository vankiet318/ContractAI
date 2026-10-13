import dataclasses
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.messages.models import ChatMessage, MessageFeedback
from app.messages.repository import ChatMessageRepository

INTERRUPTED_MESSAGE = (
    "Câu trả lời bị gián đoạn trước khi hoàn tất. Vui lòng hỏi lại."
)


class MessageNotFoundError(Exception):

    def __init__(self, message_id: str):
        super().__init__(f"Message not found: {message_id}")
        self.message_id = message_id


@dataclass
class PartialAnswer:
    text: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)


class ChatMessageService:
    """
    A message is saved as pending when the question arrives and finished
    (done or failed) when generation ends. The answer text produced so far
    is kept in memory and returned with pending messages, so a client that
    comes back mid-answer sees it. That memory belongs to this process: it
    assumes a single backend process, like the in-memory rate limiter.
    """

    def __init__(self, repository: ChatMessageRepository):
        self.repository = repository
        self._partial_answers: dict[str, PartialAnswer] = {}
        self._lock = threading.Lock()

    def start(
        self,
        session_id: str,
        question: str,
    ) -> ChatMessage:

        message = ChatMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            question=question,
            answer="",
            citations=[],
            created_at=datetime.now(),
            status="pending",
        )

        self.repository.create(message)

        with self._lock:
            self._partial_answers[message.message_id] = PartialAnswer()

        return message

    def set_citations(
        self,
        message_id: str,
        citations: list[dict[str, Any]],
    ) -> None:
        with self._lock:
            partial = self._partial_answers.get(message_id)

            if partial is not None:
                partial.citations = citations

    def append_answer(self, message_id: str, text: str) -> None:
        with self._lock:
            partial = self._partial_answers.get(message_id)

            if partial is not None:
                partial.text += text

    def complete(
        self,
        message_id: str,
        answer: str,
        citations: list[dict[str, Any]],
    ) -> None:
        self.repository.finish_pending(message_id, {
            "status": "done",
            "answer": answer,
            "citations": citations,
        })
        self._forget_partial(message_id)

    def fail(self, message_id: str, error_message: str) -> None:
        """No-op for a message that already finished."""
        self.repository.finish_pending(message_id, {
            "status": "failed",
            "error_message": error_message,
        })
        self._forget_partial(message_id)

    def fail_interrupted(self) -> int:
        """
        Run at startup: answers that were pending when the process stopped
        can never finish.
        """
        return self.repository.fail_all_pending(INTERRUPTED_MESSAGE)

    def has_pending(self, session_id: str) -> bool:
        return any(
            message.status == "pending"
            for message in self.repository.list_by_session(session_id)
        )

    def list_by_session(self, session_id: str) -> list[ChatMessage]:
        messages = sorted(
            self.repository.list_by_session(session_id),
            key=lambda message: message.created_at,
        )

        return [self._with_partial_answer(message) for message in messages]

    def set_feedback(
        self,
        session_id: str,
        message_id: str,
        feedback: MessageFeedback | None,
    ) -> None:
        updated = self.repository.set_feedback(
            session_id=session_id,
            message_id=message_id,
            feedback=feedback,
        )

        if not updated:
            raise MessageNotFoundError(message_id)

    def _with_partial_answer(self, message: ChatMessage) -> ChatMessage:
        if message.status != "pending":
            return message

        with self._lock:
            partial = self._partial_answers.get(message.message_id)

            if partial is None:
                return message

            return dataclasses.replace(
                message,
                answer=partial.text,
                citations=list(partial.citations),
            )

    def _forget_partial(self, message_id: str) -> None:
        with self._lock:
            self._partial_answers.pop(message_id, None)
