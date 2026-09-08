from app.db.models import ChatMessageORM
from app.db.session import get_db_session
from app.messages.models import ChatMessage


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

    @staticmethod
    def _to_domain(row: ChatMessageORM) -> ChatMessage:
        return ChatMessage(
            message_id=row.id,
            session_id=row.session_id,
            question=row.question,
            answer=row.answer,
            citations=row.citations,
            created_at=row.created_at,
        )
