from datetime import datetime
from typing import Any
from uuid import uuid4

from app.messages.models import ChatMessage, MessageFeedback
from app.messages.repository import ChatMessageRepository


class MessageNotFoundError(Exception):

    def __init__(self, message_id: str):
        super().__init__(f"Message not found: {message_id}")
        self.message_id = message_id


class ChatMessageService:

    def __init__(self, repository: ChatMessageRepository):
        self.repository = repository

    def create(
        self,
        session_id: str,
        question: str,
        answer: str,
        citations: list[dict[str, Any]],
    ) -> ChatMessage:

        message = ChatMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            question=question,
            answer=answer,
            citations=citations,
            created_at=datetime.now(),
        )

        self.repository.create(message)

        return message

    def list_by_session(self, session_id: str) -> list[ChatMessage]:
        return sorted(
            self.repository.list_by_session(session_id),
            key=lambda message: message.created_at,
        )

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
