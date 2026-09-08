from datetime import datetime
from uuid import uuid4

from app.auth.models import User
from app.auth.repository import UserRepository
from app.auth.security import hash_password, verify_password


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(self, email: str, password: str) -> User:
        if self.repository.get_by_email(email) is not None:
            raise ValueError(f"Email already registered: {email}")

        user = User(
            user_id=str(uuid4()),
            email=email,
            hashed_password=hash_password(password),
            created_at=datetime.now(),
        )

        self.repository.create(user)

        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repository.get_by_email(email)

        if user is None:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user
