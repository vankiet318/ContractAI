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
        )
