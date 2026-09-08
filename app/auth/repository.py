from app.auth.models import User
from app.db.models import UserORM
from app.db.session import get_db_session


class UserRepository:

    def create(self, user: User) -> None:
        with get_db_session() as db:
            db.add(
                UserORM(
                    id=user.user_id,
                    email=user.email,
                    hashed_password=user.hashed_password,
                    created_at=user.created_at,
                )
            )

    def get_by_id(self, user_id: str) -> User | None:
        with get_db_session() as db:
            row = db.get(UserORM, user_id)
            return self._to_domain(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        with get_db_session() as db:
            row = (
                db.query(UserORM)
                .filter(UserORM.email == email)
                .first()
            )
            return self._to_domain(row) if row else None

    @staticmethod
    def _to_domain(row: UserORM) -> User:
        return User(
            user_id=row.id,
            email=row.email,
            hashed_password=row.hashed_password,
            created_at=row.created_at,
        )
