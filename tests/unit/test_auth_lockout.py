from datetime import datetime, timedelta

import pytest

from app.auth.security import hash_password
from app.auth.service import (
    AccountLockedError,
    AuthService,
    EmailAlreadyRegisteredError,
    LoginLockoutPolicy,
)
from app.auth.models import User

PASSWORD = "correct-password"


class FakeUserRepository:

    def __init__(self, user: User):
        self.user = user

    def get_by_email(self, email: str) -> User | None:
        return self.user if email == self.user.email else None

    def update_login_state(self, user: User) -> None:
        self.user = user


class FakeClock:

    def __init__(self):
        self.now = datetime(2026, 10, 1, 9, 0)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def setup():
    user = User(
        user_id="u1",
        email="a@example.com",
        hashed_password=hash_password(PASSWORD),
        created_at=datetime(2026, 1, 1),
    )
    clock = FakeClock()
    service = AuthService(
        repository=FakeUserRepository(user),
        lockout_policy=LoginLockoutPolicy(
            max_failed_attempts=3,
            lock_duration=timedelta(minutes=15),
        ),
        clock=clock,
    )
    return service, clock


def fail_logins(service: AuthService, count: int) -> None:
    for _ in range(count):
        assert service.authenticate("a@example.com", "wrong-password") is None


def test_account_locks_after_max_failed_attempts_even_with_right_password(setup):
    service, _ = setup

    fail_logins(service, 3)

    with pytest.raises(AccountLockedError) as error:
        service.authenticate("a@example.com", PASSWORD)

    assert error.value.retry_after_minutes == 15


def test_lock_expires_after_lock_duration(setup):
    service, clock = setup

    fail_logins(service, 3)
    clock.now += timedelta(minutes=15, seconds=1)

    assert service.authenticate("a@example.com", PASSWORD).user_id == "u1"


def test_successful_login_resets_failed_attempts(setup):
    service, _ = setup

    fail_logins(service, 2)
    service.authenticate("a@example.com", PASSWORD)
    fail_logins(service, 2)

    assert service.authenticate("a@example.com", PASSWORD).user_id == "u1"


def test_unknown_email_returns_none(setup):
    service, _ = setup

    assert service.authenticate("nobody@example.com", PASSWORD) is None


def test_register_existing_email_raises_typed_error(setup):
    service, _ = setup

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register("a@example.com", PASSWORD)
