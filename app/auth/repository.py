from app.auth.models import User, UserRole
from app.db.models import UsageEventORM, UserORM
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
                    role=user.role,
                )
            )

    def update_login_state(self, user: User) -> None:
        with get_db_session() as db:
            row = db.get(UserORM, user.user_id)
            row.failed_login_attempts = user.failed_login_attempts
            row.locked_until = user.locked_until

    def update_role(self, user_id: str, role: UserRole) -> bool:
        with get_db_session() as db:
            row = db.get(UserORM, user_id)

            if row is None:
                return False

            row.role = role
            return True

    def unlock(self, user_id: str) -> bool:
        with get_db_session() as db:
            row = db.get(UserORM, user_id)

            if row is None:
                return False

            row.failed_login_attempts = 0
            row.locked_until = None
            return True

    def delete(self, user_id: str) -> bool:
        """
        Deletes the account and its usage history. Its sessions must already
        be gone: they own files and vectors outside the database.
        """
        with get_db_session() as db:
            row = db.get(UserORM, user_id)

            if row is None:
                return False

            db.query(UsageEventORM).filter(
                UsageEventORM.user_id == user_id
            ).delete()
            db.delete(row)
            return True

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

    def list_all(self) -> list[User]:
        with get_db_session() as db:
            rows = db.query(UserORM).order_by(UserORM.created_at).all()
            return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: UserORM) -> User:
        return User(
            user_id=row.id,
            email=row.email,
            hashed_password=row.hashed_password,
            created_at=row.created_at,
            failed_login_attempts=row.failed_login_attempts,
            locked_until=row.locked_until,
            role=row.role,
        )
