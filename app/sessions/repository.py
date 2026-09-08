from app.db.models import SessionORM
from app.db.session import get_db_session
from app.sessions.models import ChatSession


class SessionRepository:

    def create(self, session: ChatSession) -> None:
        with get_db_session() as db:
            db.add(
                SessionORM(
                    id=session.session_id,
                    user_id=session.user_id,
                    title=session.title,
                    title_is_default=session.title_is_default,
                    created_at=session.created_at,
                )
            )

    def get(self, session_id: str) -> ChatSession | None:
        with get_db_session() as db:
            row = db.get(SessionORM, session_id)
            return self._to_domain(row) if row else None

    def list_by_user(self, user_id: str) -> list[ChatSession]:
        with get_db_session() as db:
            rows = (
                db.query(SessionORM)
                .filter(SessionORM.user_id == user_id)
                .all()
            )
            return [self._to_domain(row) for row in rows]

    def update_title(
        self,
        session_id: str,
        title: str,
        title_is_default: bool,
    ) -> None:
        with get_db_session() as db:
            row = db.get(SessionORM, session_id)

            if row is None:
                raise ValueError(f"Session not found: {session_id}")

            row.title = title
            row.title_is_default = title_is_default

    def delete(self, session_id: str) -> None:
        with get_db_session() as db:
            row = db.get(SessionORM, session_id)
            if row is not None:
                db.delete(row)

    @staticmethod
    def _to_domain(row: SessionORM) -> ChatSession:
        return ChatSession(
            session_id=row.id,
            user_id=row.user_id,
            title=row.title,
            title_is_default=row.title_is_default,
            created_at=row.created_at,
        )
