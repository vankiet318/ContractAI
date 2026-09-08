from datetime import datetime
from typing import Any
from uuid import uuid4

from app.messages.models import ChatMessage
from app.messages.repository import ChatMessageRepository


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
