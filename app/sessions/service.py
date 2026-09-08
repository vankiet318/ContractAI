from datetime import datetime
from uuid import uuid4

from app.sessions.models import ChatSession
from app.sessions.repository import SessionRepository


class SessionService:

    def __init__(self, repository: SessionRepository):
        self.repository = repository

    def create(self, user_id: str, title: str) -> ChatSession:
        session = ChatSession(
            session_id=str(uuid4()),
            user_id=user_id,
            title=title,
            created_at=datetime.now(),
        )

        self.repository.create(session)

        return session

    def list_for_user(self, user_id: str) -> list[ChatSession]:
        return sorted(
            self.repository.list_by_user(user_id),
            key=lambda session: session.created_at,
            reverse=True,
        )

    def get_owned(
        self,
        session_id: str,
        user_id: str,
    ) -> ChatSession | None:

        session = self.repository.get(session_id)

        if session is None or session.user_id != user_id:
            return None

        return session

    def delete(self, session_id: str) -> None:
        self.repository.delete(session_id)

    def update_title(self, session_id: str, title: str) -> None:
        self.repository.update_title(
            session_id=session_id,
            title=title,
            title_is_default=False,
        )
