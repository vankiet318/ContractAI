import logging
from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.admin.service import AdminService
from app.api.admin import create_admin_router
from app.auth.models import User
from app.sessions.models import ChatSession
from app.logs.buffer import LogBuffer
from app.messages.models import ChatMessage, RatedMessage
from app.usage.models import DailyUsage, UsageCounts, UserUsageTotals


def make_user(user_id, role="user"):
    return User(
        user_id=user_id,
        email=f"{user_id}@example.com",
        hashed_password="x",
        created_at=datetime(2026, 1, 1),
        role=role,
    )


class FakeUserRepository:

    def __init__(self, users):
        self.users = {user.user_id: user for user in users}

    def list_all(self):
        return list(self.users.values())

    def get_by_id(self, user_id):
        return self.users.get(user_id)

    def update_role(self, user_id, role):
        if user_id not in self.users:
            return False

        self.users[user_id].role = role
        return True

    def unlock(self, user_id):
        if user_id not in self.users:
            return False

        self.users[user_id].failed_login_attempts = 0
        self.users[user_id].locked_until = None
        return True

    def delete(self, user_id):
        return self.users.pop(user_id, None) is not None


class FakeSessionService:

    def list_for_user(self, user_id):
        return [
            ChatSession(
                session_id=f"{user_id}-s1",
                user_id=user_id,
                title="a",
                created_at=datetime(2026, 1, 1),
            ),
            ChatSession(
                session_id=f"{user_id}-s2",
                user_id=user_id,
                title="b",
                created_at=datetime(2026, 1, 1),
            ),
        ]


class FakeSessionDeletionService:

    def __init__(self):
        self.deleted = []

    def delete(self, session_id, user_id):
        self.deleted.append((session_id, user_id))


class FakeUsageService:

    def window_start(self, days):
        return datetime(2026, 1, 1)

    def daily(self, days, user_id=None):
        return [DailyUsage(date=date(2026, 10, 14), queries=3, uploads=1)]

    def counts_by_user(self, days):
        return {"u1": UsageCounts(queries=3, uploads=1)}

    def totals_by_user(self):
        return {
            "u1": UserUsageTotals(
                queries=10,
                uploads=4,
                last_active_at=datetime(2026, 10, 14, 9),
            ),
        }


class FakeMessageRepository:

    def __init__(self):
        self.calls = []

    def count_feedback_since(self, since):
        return {"like": 5, "dislike": 2}

    def list_rated_since(self, since, feedback, limit, offset):
        self.calls.append((feedback, limit, offset))
        message = ChatMessage(
            message_id="m1",
            session_id="s1",
            question="Phạt vi phạm bao nhiêu?",
            answer="Không tìm thấy.",
            citations=[CITATION],
            created_at=datetime(2026, 10, 14, 9),
            feedback=feedback,
        )
        rated = RatedMessage(
            message=message,
            user_id="u1",
            user_email="u1@example.com",
            session_title="Hợp đồng thuê",
        )
        return [rated], 7


CITATION = {
    "source_id": "S1",
    "chunk_id": "c1",
    "document_id": "d1",
    "page_start": 3,
    "page_end": 3,
    "section_number": "5",
    "section_title": "Phạt vi phạm",
    "text_snippet": "Bên vi phạm chịu phạt 8%...",
}


def build_client(
    current_user=None,
    message_repository=None,
    log_buffer=None,
    users=None,
    session_deletion_service=None,
):
    admin = make_user("admin", role="admin")
    current_user = current_user or admin

    def require_admin():
        if not current_user.is_admin:
            raise HTTPException(status_code=403)
        return current_user

    service = AdminService(
        user_repository=FakeUserRepository(users or [admin, make_user("u1")]),
        message_repository=message_repository or FakeMessageRepository(),
        usage_service=FakeUsageService(),
        session_service=FakeSessionService(),
        session_deletion_service=(
            session_deletion_service or FakeSessionDeletionService()
        ),
        clock=lambda: datetime(2026, 10, 14, 12),
    )

    app = FastAPI()
    app.include_router(
        create_admin_router(
            admin_service=service,
            log_buffer=log_buffer or LogBuffer(capacity=10),
            require_admin=require_admin,
        ),
        prefix="/admin",
    )
    return TestClient(app)


def test_non_admin_is_forbidden():
    client = build_client(current_user=make_user("u1"))

    assert client.get("/admin/overview").status_code == 403
    assert client.get("/admin/users").status_code == 403


def test_overview_sums_the_window():
    body = build_client().get("/admin/overview?days=7").json()

    assert body["days"] == 7
    assert body["total_users"] == 2
    assert body["active_users"] == 1
    assert (body["queries"], body["uploads"]) == (3, 1)
    assert (body["likes"], body["dislikes"]) == (5, 2)
    assert body["daily"] == [{"date": "2026-10-14", "queries": 3, "uploads": 1}]


def test_users_include_window_and_total_usage():
    users = {
        user["user_id"]: user
        for user in build_client().get("/admin/users").json()
    }

    assert users["u1"]["queries"] == 3
    assert users["u1"]["uploads"] == 1
    assert users["u1"]["total_queries"] == 10
    assert users["u1"]["total_uploads"] == 4
    assert users["admin"]["queries"] == 0
    assert users["admin"]["last_active_at"] is None


def test_window_is_limited():
    assert build_client().get("/admin/overview?days=0").status_code == 422
    assert build_client().get("/admin/overview?days=366").status_code == 422


def test_user_usage_of_unknown_user_is_404():
    assert build_client().get("/admin/users/nobody/usage").status_code == 404


def test_admin_can_change_another_users_role():
    response = build_client().patch(
        "/admin/users/u1/role",
        json={"role": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_cannot_change_own_role():
    response = build_client().patch(
        "/admin/users/admin/role",
        json={"role": "user"},
    )

    assert response.status_code == 400


def test_feedback_lists_rated_answers_with_their_sources():
    messages = FakeMessageRepository()

    body = build_client(message_repository=messages).get(
        "/admin/feedback?rating=dislike&limit=10&offset=20"
    ).json()

    assert messages.calls == [("dislike", 10, 20)]
    assert body["total"] == 7
    item = body["items"][0]
    assert item["feedback"] == "dislike"
    assert item["user_email"] == "u1@example.com"
    assert item["session_title"] == "Hợp đồng thuê"
    assert item["citations"][0]["text_snippet"] == "Bên vi phạm chịu phạt 8%..."


def test_feedback_rejects_unknown_rating():
    response = build_client().get("/admin/feedback?rating=meh")

    assert response.status_code == 422


def test_logs_are_returned_newest_first():
    buffer = LogBuffer(capacity=10)
    logger = logging.getLogger("test.admin.logs")
    logger.handlers = [buffer]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.info("older")
    logger.error("newer")

    body = build_client(log_buffer=buffer).get("/admin/logs").json()

    assert [(e["level"], e["message"]) for e in body] == [
        ("ERROR", "newer"),
        ("INFO", "older"),
    ]


def test_logs_are_admin_only():
    client = build_client(current_user=make_user("u1"))

    assert client.get("/admin/logs").status_code == 403


def test_delete_user_removes_their_sessions_and_account():
    deletions = FakeSessionDeletionService()
    client = build_client(session_deletion_service=deletions)

    assert client.delete("/admin/users/u1").status_code == 204
    assert deletions.deleted == [("u1-s1", "u1"), ("u1-s2", "u1")]
    assert client.get("/admin/users/u1/usage").status_code == 404


def test_admin_cannot_delete_themselves():
    deletions = FakeSessionDeletionService()
    client = build_client(session_deletion_service=deletions)

    assert client.delete("/admin/users/admin").status_code == 400
    assert deletions.deleted == []


def test_delete_unknown_user_is_404():
    assert build_client().delete("/admin/users/nobody").status_code == 404


def test_unlock_clears_a_login_lock():
    locked = make_user("u1")
    locked.failed_login_attempts = 5
    locked.locked_until = datetime(2026, 10, 14, 13)
    client = build_client(users=[make_user("admin", role="admin"), locked])

    before = client.get("/admin/users/u1/usage").json()["user"]
    response = client.post("/admin/users/u1/unlock")

    assert before["is_locked"] is True
    assert response.status_code == 200
    assert response.json()["is_locked"] is False
    assert locked.failed_login_attempts == 0
