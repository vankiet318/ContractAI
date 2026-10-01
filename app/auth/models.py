from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    user_id: str
    email: str
    hashed_password: str
    created_at: datetime
    failed_login_attempts: int = 0
    locked_until: datetime | None = None

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now
