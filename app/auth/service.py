import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable
from uuid import uuid4

from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.security import hash_password, verify_password

# Checked when the email is unknown so a login takes about as long as for
# a real account; otherwise response time reveals which emails exist.
_TIMING_EQUALIZER_HASH = hash_password("timing-equalizer-password")


class EmailAlreadyRegisteredError(Exception):
    pass


class AccountLockedError(Exception):

    def __init__(self, retry_after_minutes: int):
        super().__init__(
            f"Account locked, retry after {retry_after_minutes} minutes"
        )
        self.retry_after_minutes = retry_after_minutes


@dataclass(frozen=True)
class LoginLockoutPolicy:
    max_failed_attempts: int
    lock_duration: timedelta


class AuthService:

    def __init__(
        self,
        repository: UserRepository,
        lockout_policy: LoginLockoutPolicy,
        clock: Callable[[], datetime] = datetime.now,
    ):
        self.repository = repository
        self.lockout_policy = lockout_policy
        self.clock = clock

    def register(self, email: str, password: str) -> User:
        if self.repository.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(email)

        user = User(
            user_id=str(uuid4()),
            email=email,
            hashed_password=hash_password(password),
            created_at=self.clock(),
        )

        self.repository.create(user)

        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repository.get_by_email(email)

        if user is None:
            verify_password(password, _TIMING_EQUALIZER_HASH)
            return None

        self._ensure_not_locked(user)

        if not verify_password(password, user.hashed_password):
            self._record_failed_login(user)
            return None

        self._reset_failed_logins(user)

        return user

    def _ensure_not_locked(self, user: User) -> None:
        now = self.clock()

        if not user.is_locked(now):
            return

        remaining = user.locked_until - now

        raise AccountLockedError(
            retry_after_minutes=max(1, math.ceil(remaining.total_seconds() / 60))
        )

    def _record_failed_login(self, user: User) -> None:
        user.failed_login_attempts += 1

        if user.failed_login_attempts >= self.lockout_policy.max_failed_attempts:
            user.locked_until = self.clock() + self.lockout_policy.lock_duration
            user.failed_login_attempts = 0

        self.repository.update_login_state(user)

    def _reset_failed_logins(self, user: User) -> None:
        if user.failed_login_attempts == 0 and user.locked_until is None:
            return

        user.failed_login_attempts = 0
        user.locked_until = None

        self.repository.update_login_state(user)
