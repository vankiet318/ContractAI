from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.admin.service import AdminService
from app.api.admin import create_admin_router
from app.auth.models import User
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

    def count_feedback_since(self, since):
        return {"like": 5, "dislike": 2}


def build_client(current_user=None):
    admin = make_user("admin", role="admin")
    current_user = current_user or admin

    def require_admin():
        if not current_user.is_admin:
            raise HTTPException(status_code=403)
        return current_user

    service = AdminService(
        user_repository=FakeUserRepository([admin, make_user("u1")]),
        message_repository=FakeMessageRepository(),
        usage_service=FakeUsageService(),
    )

    app = FastAPI()
    app.include_router(
        create_admin_router(admin_service=service, require_admin=require_admin),
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
