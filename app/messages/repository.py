from datetime import datetime
from typing import Any

from sqlalchemy import func

from app.db.models import ChatMessageORM
from app.db.session import get_db_session
from app.messages.models import ChatMessage, MessageFeedback


class ChatMessageRepository:

    def create(self, message: ChatMessage) -> None:
        with get_db_session() as db:
            db.add(
                ChatMessageORM(
                    id=message.message_id,
                    session_id=message.session_id,
                    question=message.question,
                    answer=message.answer,
                    citations=message.citations,
                    created_at=message.created_at,
                    feedback=message.feedback,
                    status=message.status,
                    error_message=message.error_message,
                )
            )

    def list_by_session(self, session_id: str) -> list[ChatMessage]:
        with get_db_session() as db:
            rows = (
                db.query(ChatMessageORM)
                .filter(ChatMessageORM.session_id == session_id)
                .all()
            )
            return [self._to_domain(row) for row in rows]

    def finish_pending(
        self,
        message_id: str,
        values: dict[str, Any],
    ) -> bool:
        """
        Updates the message only while it is still pending, so a finished
        answer is never overwritten by a later failure.
        """
        with get_db_session() as db:
            updated_rows = (
                db.query(ChatMessageORM)
                .filter(
                    ChatMessageORM.id == message_id,
                    ChatMessageORM.status == "pending",
                )
                .update(values)
            )
            return updated_rows > 0

    def fail_all_pending(self, error_message: str) -> int:
        with get_db_session() as db:
            return (
                db.query(ChatMessageORM)
                .filter(ChatMessageORM.status == "pending")
                .update({
                    "status": "failed",
                    "error_message": error_message,
                })
            )

    def set_feedback(
        self,
        session_id: str,
        message_id: str,
        feedback: MessageFeedback | None,
    ) -> bool:
        with get_db_session() as db:
            updated_rows = (
                db.query(ChatMessageORM)
                .filter(
                    ChatMessageORM.id == message_id,
                    ChatMessageORM.session_id == session_id,
                )
                .update({"feedback": feedback})
            )
            return updated_rows > 0

    def count_feedback_since(self, since: datetime) -> dict[str, int]:
        """Messages asked since `since`, counted by feedback given."""
        with get_db_session() as db:
            rows = (
                db.query(ChatMessageORM.feedback, func.count())
                .filter(
                    ChatMessageORM.created_at >= since,
                    ChatMessageORM.feedback.is_not(None),
                )
                .group_by(ChatMessageORM.feedback)
                .all()
            )
            return {feedback: count for feedback, count in rows}

    @staticmethod
    def _to_domain(row: ChatMessageORM) -> ChatMessage:
        return ChatMessage(
            message_id=row.id,
            session_id=row.session_id,
            question=row.question,
            answer=row.answer,
            citations=row.citations,
            created_at=row.created_at,
            feedback=row.feedback,
            status=row.status,
            error_message=row.error_message,
        )
