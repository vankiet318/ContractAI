from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.auth import create_auth_router
from app.auth.models import User
from app.auth.service import AccountLockedError


def no_limit() -> None:
    return None


def always_limited() -> None:
    raise HTTPException(status_code=429, detail="limited")


def build_client(
    auth_service,
    login_rate_limit=no_limit,
    current_user=None,
) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_auth_router(
            auth_service=auth_service,
            login_rate_limit=login_rate_limit,
            register_rate_limit=no_limit,
            get_current_user=lambda: current_user,
        ),
        prefix="/auth",
    )
    return TestClient(app)


def test_password_over_72_bytes_is_rejected_with_422_not_500():
    client = build_client(SimpleNamespace())

    # 25 Vietnamese characters of 3 bytes each = 75 bytes.
    response = client.post(
        "/auth/login",
        json={"email": "a@example.com", "password": "ệ" * 25},
    )

    assert response.status_code == 422


def test_locked_account_returns_429():
    def authenticate(email, password):
        raise AccountLockedError(retry_after_minutes=7)

    client = build_client(SimpleNamespace(authenticate=authenticate))

    response = client.post(
        "/auth/login",
        json={"email": "a@example.com", "password": "whatever-password"},
    )

    assert response.status_code == 429
    assert "7 phút" in response.json()["detail"]


def test_login_rate_limit_runs_before_authentication():
    client = build_client(SimpleNamespace(), login_rate_limit=always_limited)

    response = client.post(
        "/auth/login",
        json={"email": "a@example.com", "password": "whatever-password"},
    )

    assert response.status_code == 429


def test_me_returns_the_role_of_the_current_user():
    user = User(
        user_id="u1",
        email="admin@example.com",
        hashed_password="x",
        created_at=datetime(2026, 1, 1),
        role="admin",
    )

    response = build_client(SimpleNamespace(), current_user=user).get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "u1",
        "email": "admin@example.com",
        "role": "admin",
    }
