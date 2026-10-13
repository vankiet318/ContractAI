from app.sessions.models import ChatSession
from app.sessions.service import SessionService


class FakeSessionRepository:

    def __init__(self):
        self.sessions: dict[str, ChatSession] = {}
        self.non_empty: set[str] = set()

    def create(self, session: ChatSession) -> None:
        self.sessions[session.session_id] = session

    def find_newest_empty(self, user_id: str) -> ChatSession | None:
        empty = [
            session
            for session in self.sessions.values()
            if session.user_id == user_id
            and session.session_id not in self.non_empty
        ]
        return max(empty, key=lambda s: s.created_at, default=None)


def test_new_chat_reuses_the_empty_session():
    service = SessionService(repository=FakeSessionRepository())

    first = service.get_or_create_empty(user_id="u1", title="Đoạn chat mới")
    second = service.get_or_create_empty(user_id="u1", title="Đoạn chat mới")

    assert second.session_id == first.session_id


def test_new_chat_is_created_once_the_session_is_used():
    repository = FakeSessionRepository()
    service = SessionService(repository=repository)

    first = service.get_or_create_empty(user_id="u1", title="Đoạn chat mới")
    repository.non_empty.add(first.session_id)

    second = service.get_or_create_empty(user_id="u1", title="Đoạn chat mới")

    assert second.session_id != first.session_id


def test_empty_session_of_another_user_is_not_reused():
    service = SessionService(repository=FakeSessionRepository())

    mine = service.get_or_create_empty(user_id="u1", title="Đoạn chat mới")
    theirs = service.get_or_create_empty(user_id="u2", title="Đoạn chat mới")

    assert theirs.session_id != mine.session_id
